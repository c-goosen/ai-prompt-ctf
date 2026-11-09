"""Upload the System 1 dataset to Hugging Face for Unsloth Decision model training.

A new repo starts private and is re-downloaded and checked. Only then does
--public make it public. --update replaces the files in an existing repo and
leaves its visibility alone.

    uv run push_system1_dataset.py          # private upload and verification
    uv run push_system1_dataset.py --public # also make the new repo public
    uv run push_system1_dataset.py --update # update the existing repo
"""

import argparse
import json
from pathlib import Path

import pandas as pd
from datasets import Dataset, DatasetDict, load_dataset
from huggingface_hub import DatasetCard, HfApi

from system1_battery import PROMPT_TYPES, QUESTIONS, gold_for

DEFAULT_DATA = Path(__file__).parent / "data" / "system1_guardrails"
DEFAULT_REPO = "cgoosen/system1-prompt-injection"
SPLITS = ("train", "evaluation", "test")
COLUMNS = [
    "state",
    "questions",
    "gold",
    "source",
    "subsource",
    "attack_type",
    "group_id",
]
DOCS_URL = (
    "https://unsloth.ai/docs/basics/train-your-own-decision-model-with-unsloth"
)
JEV_DOCS_URL = "https://docs.typesafe.ai/primitives"


def to_decision_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Build Jev-format rows. The prompt lives in `state` and nowhere else."""
    rows = df.copy()
    rows["state"] = rows["text"].map(
        lambda text: json.dumps({"user_message": text}, ensure_ascii=False)
    )
    rows["questions"] = json.dumps(QUESTIONS)
    rows["gold"] = rows["attack_type"].map(
        lambda kind: json.dumps(gold_for(kind))
    )
    return rows[COLUMNS]


def load_rows(data_dir: Path) -> dict[str, pd.DataFrame]:
    return {
        split: to_decision_rows(pd.read_parquet(data_dir / f"{split}.parquet"))
        for split in SPLITS
    }


def card_body(rows: dict[str, pd.DataFrame], report: dict, repo: str) -> str:
    names = list(QUESTIONS["prompt_type"]["criteria"])
    header = " | ".join(names)
    table = []
    for split, frame in rows.items():
        counts = frame["attack_type"].map(PROMPT_TYPES).value_counts()
        cells = " | ".join(f"{counts.get(name, 0):,}" for name in names)
        table.append(f"| `{split}` | {cells} | {len(frame):,} |")
    split_rows = "\n".join(table)
    source_rows = "\n".join(
        f"- [{source_repo}](https://huggingface.co/datasets/{source_repo})"
        for name, source_repo in report["source_repos"].items()
        if name != "curated"
    )
    source_rows += (
        "\n- `curated`: harmless password and security prompts written for this "
        "dataset, to teach that those words alone aren't an attack"
    )
    excluded = ", ".join(report["excluded_htb_subsources"]) or "none"
    duplicates = report["duplicates"]
    return f"""# System 1 prompt injection dataset

A deduplicated dataset for fine-tuning a prompt injection
[Decision model with Unsloth]({DOCS_URL}), using
[Jev-style questions]({JEV_DOCS_URL}). Each prompt gets two decisions:

- **`is_malicious` (Noul):** "{QUESTIONS['is_malicious']['instructions']}"
- **`prompt_type` (Choice):** "{QUESTIONS['prompt_type']['instructions']}"

**For non-commercial educational use.** It was built for PwnGPT, a prompt injection
CTF. It contains real prompt injection, jailbreak and harmful request text, some of it
offensive.

## Splits

| Split | {header} | Total |
|---|{'---|' * len(names)}---|
{split_rows}

Use `evaluation` to choose a checkpoint and `test` once for the final score.

```python
from datasets import load_dataset
from unsloth import FastDecisionModel

train = load_dataset("{repo}", split="train")
items, report = FastDecisionModel.build_dataset(train, tokenizer, model)
```

In Unsloth Studio, set **Train as** to **Decision model** and pick this dataset.

## Columns

- `state`: the prompt, as a JSON string such as `{{"user_message": "..."}}`.
- `questions`: the two questions, as a JSON string.
- `gold`: the answers, as a JSON string.
- `source`, `subsource`, `attack_type`: where the row came from and its original type.
  Don't pass these to a model, because they reveal the answer.
- `group_id`: the near-duplicate cluster. Rows in a cluster stay in one split.

## Labels

Answers come from the source datasets, not from a model. `obfuscated` has few rows, so
expect weaker results on it. Prompts from sources that only say "attack" are labelled
`injection`, so some of them may really be jailbreaks.

## Sources

{source_rows}

**Licences:** each upstream source keeps its own licence, whatever the tag on the
dataset that collected it. The `subsource` column names the origin of HTB rows. Some
are non-commercial, including `PKU-SafeRLHF`, `BeaverTails` and `ToxicChat`
(CC BY-NC 4.0), and `ALERT` (CC BY-NC-SA 4.0). Others, including `jayavibhav-PI` and
`safe-guard-PI`, have no licence tag on Hugging Face. Check these terms before reusing
this dataset, and don't use it commercially.

Removed from the HTB rows: {excluded}.

## Processing

- Exact duplicates were removed, ignoring case, spacing and punctuation. Texts with
  conflicting labels were dropped ({duplicates['label_conflict_rows_removed']} rows).
- Near-duplicates were removed with MinHash at
  {duplicates['near']['threshold']} similarity
  ({duplicates['near']['near_duplicates_dropped']:,} rows).
- `[System: ...]` wrappers were stripped from SPML and TensorTrust rows, because they
  appeared almost only on attacks and would give away the label.
- HTB upstream sources were capped at {report['htb_subsource_cap']['cap']:,} rows per
  class, and texts over 8,000 characters were dropped.

## Known limitations

- **Keyword bias.** Nearly every prompt that mentions "password" is labelled malicious.
  Expect false positives on harmless security questions, and test for them separately,
  because the `test` split has the same skew.
- **Other signals.** Malicious prompts tend to be longer, and more of them are all
  lowercase. `### Instruction:` templates also mark many `ALERT` rows.
- **Residual near-duplicates.** MinHash is approximate, so a small share of held-out
  rows may still closely resemble a training row.
"""


def verify_upload(repo: str, rows: dict[str, pd.DataFrame]) -> None:
    """Re-download every split and compare it with what should have gone up."""
    for split, expected in rows.items():
        remote = load_dataset(
            repo, split=split, download_mode="force_redownload"
        )
        if remote.column_names != COLUMNS:
            raise RuntimeError(
                f"{split}: unexpected columns {remote.column_names}"
            )
        pairs = sorted(zip(remote["state"], remote["gold"]))
        if pairs != sorted(zip(expected["state"], expected["gold"])):
            raise RuntimeError(
                f"{split}: uploaded rows differ from the local build"
            )
        print(f"Verified {split}: {remote.num_rows} rows")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    visibility = parser.add_mutually_exclusive_group()
    visibility.add_argument("--public", action="store_true")
    visibility.add_argument("--update", action="store_true")
    args = parser.parse_args()

    report = json.loads((args.data / "report.json").read_text())
    rows = load_rows(args.data)
    api = HfApi()
    exists = api.repo_exists(args.repo, repo_type="dataset")
    if exists and not args.update:
        raise SystemExit(
            f"{args.repo} already exists; use --update to replace it"
        )
    if args.update and not exists:
        raise SystemExit(f"{args.repo} doesn't exist; nothing to update")
    if not exists:
        api.create_repo(args.repo, repo_type="dataset", private=True)

    dataset = DatasetDict(
        {
            split: Dataset.from_pandas(frame, preserve_index=False)
            for split, frame in rows.items()
        }
    )
    dataset.push_to_hub(args.repo)

    # Editing the generated card keeps its split metadata. Without that, the Hub
    # would read a file named "evaluation" as the validation split.
    card = DatasetCard.load(args.repo, repo_type="dataset")
    card.text = card_body(rows, report, args.repo)
    card.data.license = "other"
    card.data.task_categories = ["text-classification"]
    card.data.tags = [
        "prompt-injection",
        "jailbreak",
        "llm-security",
        "unsloth",
    ]
    card.push_to_hub(args.repo, repo_type="dataset")

    verify_upload(args.repo, rows)

    if args.public:
        api.update_repo_settings(args.repo, repo_type="dataset", private=False)
    print(f"Done: https://huggingface.co/datasets/{args.repo}")


if __name__ == "__main__":
    main()
