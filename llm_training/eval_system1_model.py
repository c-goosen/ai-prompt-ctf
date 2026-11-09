"""Score a trained System 1 Decision model on the held-out test split.

Sends every test row to the Unsloth Studio Decision API (POST /v1/systemone),
then compares the answers with the gold labels for both questions:

- is_malicious (Noul): accuracy, precision, recall, F1, false positive rate and
  ROC AUC, at several thresholds
- prompt_type (Choice): accuracy, macro F1, per-class results and a confusion
  matrix

Run it from llm_training/, with training stopped, because the Decision API waits
while a training run holds the GPU:

    uv run eval_system1_model.py                        # the configured model
    uv run eval_system1_model.py --model <fine-tune>    # a named checkpoint
    uv run eval_system1_model.py --probes               # hand-labelled probes
    uv run eval_system1_model.py --limit 200            # quick sample

The API key is read from UNSLOTH_API_KEY or from llm_training/.env, and is never
printed. Answers are cached in the output folder, so an interrupted run resumes
where it stopped.
"""

import argparse
import hashlib
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx
import pandas as pd
from datasets import load_dataset
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
)

from push_system1_dataset import to_decision_rows
from system1_battery import QUESTIONS

HERE = Path(__file__).parent
DEFAULT_REPO = "cgoosen/system1-prompt-injection"
DEFAULT_URL = "http://100.122.67.1:8888"
PROBES_FILE = HERE / "system1_probes.jsonl"
THRESHOLDS = (0.3, 0.5, 0.7)
PROMPT_TYPES = list(QUESTIONS["prompt_type"]["criteria"])
RETRY_STATUSES = {429, 500, 502, 503, 504}


def api_key() -> str | None:
    if key := os.environ.get("UNSLOTH_API_KEY"):
        return key
    env_file = HERE / ".env"
    if env_file.exists():
        for line in env_file.read_text("utf-8").splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "UNSLOTH_API_KEY":
                return value.strip().strip("'\"")
    return None


def load_test_rows(args) -> pd.DataFrame:
    """Return rows with message, is_malicious, prompt_type and grouping columns."""
    if args.probes:
        rows = pd.read_json(PROBES_FILE, lines=True)
        rows["source"] = "probes"
        rows["subsource"] = rows["group"]
    else:
        if args.data:
            # A local build has text and attack_type; convert it as the upload does.
            rows = to_decision_rows(
                pd.read_parquet(args.data / f"{args.split}.parquet")
            )
        else:
            rows = load_dataset(args.repo, split=args.split).to_pandas()
        rows["message"] = rows["state"].map(
            lambda s: json.loads(s)["user_message"]
        )
        gold = rows["gold"].map(json.loads)
        rows["is_malicious"] = gold.map(
            lambda g: g["is_malicious"]["label"] == "true"
        )
        rows["prompt_type"] = gold.map(lambda g: g["prompt_type"]["label"])
    rows = rows.reset_index(drop=True)
    if args.limit and args.limit < len(rows):
        rows = rows.sample(n=args.limit, random_state=args.seed).reset_index(
            drop=True
        )
    return rows


def cache_key(model: str, message: str) -> str:
    payload = json.dumps([model, message, QUESTIONS], ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class DecisionClient:
    def __init__(self, url: str, model: str, key: str | None, retries: int):
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        self.client = httpx.Client(base_url=url, headers=headers, timeout=120)
        self.model = model
        self.retries = retries

    def decide(self, message: str) -> dict:
        body = {
            "model": self.model,
            "state": {"user_message": message},
            "questions": QUESTIONS,
        }
        for attempt in range(self.retries + 1):
            try:
                response = self.client.post("/v1/systemone", json=body)
            except httpx.TransportError:
                if attempt == self.retries:
                    raise
                time.sleep(2**attempt)
                continue
            if (
                response.status_code in RETRY_STATUSES
                and attempt < self.retries
            ):
                wait = float(response.headers.get("Retry-After", 2**attempt))
                time.sleep(min(wait, 60))
                continue
            if response.status_code != 200:
                raise RuntimeError(
                    f"Decision API returned {response.status_code}: {response.text[:300]}"
                )
            return response.json()["answers"]
        raise RuntimeError("unreachable")


def run_predictions(
    rows: pd.DataFrame, client: DecisionClient, cache_file: Path, workers: int
):
    cache = {}
    if cache_file.exists():
        for line in cache_file.read_text("utf-8").splitlines():
            entry = json.loads(line)
            cache[entry["key"]] = entry["answers"]

    keys = [cache_key(client.model, message) for message in rows["message"]]
    todo = {
        key: message
        for key, message in zip(keys, rows["message"])
        if key not in cache
    }
    print(f"{len(rows) - len(todo)} cached, {len(todo)} to request")

    lock = threading.Lock()
    started = time.monotonic()
    with (
        cache_file.open("a", encoding="utf-8") as out,
        ThreadPoolExecutor(workers) as pool,
    ):
        futures = {
            pool.submit(client.decide, message): key
            for key, message in todo.items()
        }
        for done, future in enumerate(as_completed(futures), start=1):
            key = futures[future]
            answers = future.result()
            with lock:
                cache[key] = answers
                out.write(json.dumps({"key": key, "answers": answers}) + "\n")
                out.flush()
            if done % 50 == 0 or done == len(todo):
                rate = done / (time.monotonic() - started)
                left = (len(todo) - done) / rate if rate else 0
                print(
                    f"  {done}/{len(todo)}  {rate:.1f} rows/s  ~{left / 60:.0f} min left"
                )
    return [cache[key] for key in keys]


def binary_metrics(gold: pd.Series, predicted: pd.Series) -> dict:
    tp = int((gold & predicted).sum())
    fp = int((~gold & predicted).sum())
    fn = int((gold & ~predicted).sum())
    tn = int((~gold & ~predicted).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "accuracy": (tp + tn) / len(gold),
        "precision": precision,
        "recall": recall,
        "f1": (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        ),
        "false_positive_rate": fp / (fp + tn) if fp + tn else 0.0,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def evaluate(rows: pd.DataFrame, threshold: float) -> dict:
    gold = rows["is_malicious"].astype(bool)
    report = {"rows": len(rows), "noul": {}, "choice": {}}

    if gold.nunique() == 2:
        report["noul"]["roc_auc"] = roc_auc_score(gold, rows["p_malicious"])
    for cut in THRESHOLDS:
        report["noul"][f"at_{cut}"] = binary_metrics(
            gold, rows["p_malicious"] >= cut
        )

    labels = PROMPT_TYPES
    choice = classification_report(
        rows["prompt_type"],
        rows["pred_type"],
        labels=labels,
        output_dict=True,
        zero_division=0,
    )
    report["choice"] = {
        "accuracy": float((rows["prompt_type"] == rows["pred_type"]).mean()),
        "macro_f1": choice["macro avg"]["f1-score"],
        "per_class": {name: choice[name] for name in labels},
        "confusion_matrix": {
            "labels": labels,
            "rows_are_gold": confusion_matrix(
                rows["prompt_type"], rows["pred_type"], labels=labels
            ).tolist(),
        },
        # Treat any non-benign choice as "malicious", to compare with the Noul answer.
        "as_binary": binary_metrics(gold, rows["pred_type"] != "benign"),
    }
    flagged = rows["p_malicious"] >= threshold
    report["disagreement_rate"] = float(
        (flagged != (rows["pred_type"] != "benign")).mean()
    )

    benign = rows[~gold]
    mentions = benign["message"].str.contains("password", case=False)
    report["benign_password_false_positives"] = {
        f"at_{cut}": {
            "rows": int(mentions.sum()),
            "flagged": int((benign.loc[mentions, "p_malicious"] >= cut).sum()),
        }
        for cut in THRESHOLDS
    }

    by_source = {}
    for (source, subsource), group in rows.fillna({"subsource": ""}).groupby(
        ["source", "subsource"]
    ):
        name = f"{source}/{subsource}" if subsource else source
        by_source[name] = {
            "rows": len(group),
            "noul_accuracy": float(
                (
                    (group["p_malicious"] >= threshold) == group["is_malicious"]
                ).mean()
            ),
            "choice_accuracy": float(
                (group["prompt_type"] == group["pred_type"]).mean()
            ),
        }
    report["by_source"] = by_source
    return report


def print_summary(report: dict, threshold: float) -> None:
    noul = report["noul"]
    print(f"\n{report['rows']:,} rows")
    print("\nis_malicious (Noul)")
    if "roc_auc" in noul:
        print(f"  ROC AUC {noul['roc_auc']:.4f}")
    print("  threshold  accuracy  precision  recall  F1      FPR")
    for cut in THRESHOLDS:
        m = noul[f"at_{cut}"]
        print(
            f"  {cut:<9}  {m['accuracy']:.4f}    {m['precision']:.4f}     "
            f"{m['recall']:.4f}  {m['f1']:.4f}  {m['false_positive_rate']:.4f}"
        )

    choice = report["choice"]
    print("\nprompt_type (Choice)")
    print(
        f"  accuracy {choice['accuracy']:.4f}  macro F1 {choice['macro_f1']:.4f}"
    )
    print("  class       precision  recall  F1      rows")
    for name, m in choice["per_class"].items():
        print(
            f"  {name:<10}  {m['precision']:.4f}     {m['recall']:.4f}  "
            f"{m['f1-score']:.4f}  {int(m['support'])}"
        )
    labels = choice["confusion_matrix"]["labels"]
    print("\n  confusion (rows gold, columns predicted)")
    print("  " + " " * 11 + "".join(f"{name[:9]:>10}" for name in labels))
    for name, counts in zip(
        labels, choice["confusion_matrix"]["rows_are_gold"]
    ):
        print(f"  {name:<11}" + "".join(f"{count:>10}" for count in counts))

    print(
        f"\nNoul and Choice disagree on {report['disagreement_rate']:.1%} of rows "
        f"(Noul at {threshold})"
    )
    print("Benign prompts mentioning 'password' flagged as malicious:")
    for cut, m in report["benign_password_false_positives"].items():
        print(f"  {cut}: {m['flagged']}/{m['rows']}")

    print("\nBy source, 10+ rows (worst Noul accuracy first)")
    ranked = sorted(
        report["by_source"].items(), key=lambda item: item[1]["noul_accuracy"]
    )
    for name, m in [item for item in ranked if item[1]["rows"] >= 10][:15]:
        print(
            f"  {name:<40} {m['rows']:>5} rows  Noul {m['noul_accuracy']:.3f}  "
            f"Choice {m['choice_accuracy']:.3f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--url", default=os.environ.get("UNSLOTH_URL", DEFAULT_URL)
    )
    parser.add_argument(
        "--model",
        default="default",
        help="Studio model name; 'default' is the one picked in settings",
    )
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument(
        "--split", default="test", choices=["train", "evaluation", "test"]
    )
    parser.add_argument(
        "--data", type=Path, help="local build folder instead of the Hub"
    )
    parser.add_argument(
        "--probes",
        action="store_true",
        help=f"score {PROBES_FILE.name} instead of a dataset split",
    )
    parser.add_argument(
        "--limit", type=int, help="score a random sample of this many rows"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Noul threshold for per-source results and misses",
    )
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=HERE / "data" / "eval")
    args = parser.parse_args()

    rows = load_test_rows(args)
    name = "probes" if args.probes else args.split
    out_dir = args.output / f"{args.model.replace('/', '_')}_{name}"
    out_dir.mkdir(parents=True, exist_ok=True)

    client = DecisionClient(args.url, args.model, api_key(), args.retries)
    answers = run_predictions(
        rows, client, out_dir / "answers.jsonl", args.workers
    )
    rows["p_malicious"] = [a["is_malicious"]["noul"] for a in answers]
    rows["pred_type"] = [a["prompt_type"]["choice"] for a in answers]
    rows["p_type"] = [
        a["prompt_type"]["probabilities"].get(a["prompt_type"]["choice"])
        for a in answers
    ]

    report = evaluate(rows, args.threshold)
    report["settings"] = {
        "model": args.model,
        "data": (
            "probes"
            if args.probes
            else str(args.data or f"{args.repo}:{args.split}")
        ),
        "limit": args.limit,
        "threshold": args.threshold,
    }
    print_summary(report, args.threshold)

    (out_dir / "report.json").write_text(json.dumps(report, indent=2))
    wrong = (rows["p_malicious"] >= args.threshold) != rows["is_malicious"]
    wrong |= rows["pred_type"] != rows["prompt_type"]
    columns = [
        "message",
        "is_malicious",
        "p_malicious",
        "prompt_type",
        "pred_type",
        "p_type",
        "source",
        "subsource",
    ]
    rows.loc[wrong, columns].to_json(
        out_dir / "mistakes.jsonl",
        orient="records",
        lines=True,
        force_ascii=False,
    )
    print(
        f"\nWrote {out_dir / 'report.json'} and {int(wrong.sum())} mistakes to "
        f"{out_dir / 'mistakes.jsonl'}"
    )


if __name__ == "__main__":
    main()
