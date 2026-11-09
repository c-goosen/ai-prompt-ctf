"""Build a deduplicated train/evaluation/test dataset for a System 1 classifier.

"System 1" here means the fast, automatic first decision on a prompt: a small
binary classifier (0 = SAFE, 1 = INJECTION) that runs before any slower check.

Run it from llm_training/:

    uv run build_system1_dataset.py
    uv run build_system1_dataset.py --exclude rogue   # drop the CC-BY-NC source

    # The build behind the public cgoosen/system1-prompt-injection dataset:
    uv run build_system1_dataset.py --exclude rogue \
        --exclude-htb-subsources WildGuardMix WildJailbreak \
        --output data/system1_prompt_injection_public

    # The build behind the guardrail battery. See system1_battery.py.
    uv run build_system1_dataset.py --exclude rogue \
        --exclude-htb-subsources WildGuardMix WildJailbreak \
        --harmful-subsources Aegis-2.0 ALERT AttaQ BeaverTails CategoricalHarmfulQA \
            Do-Not-Answer JBB-Behaviors JailBreakV-28k OR-Bench PKU-SafeRLHF \
            RealToxicityPrompts RedBench SafeMTData ToxicChat WMDP \
        --output data/system1_guardrails

rogue-security/prompt-injections-benchmark is gated. Accept its terms on Hugging
Face and run `hf auth login` first, or exclude it.

Load the result with:

    load_dataset("parquet", data_files={
        "train": "data/system1_prompt_injection/train.parquet",
        "evaluation": "data/system1_prompt_injection/evaluation.parquet",
        "test": "data/system1_prompt_injection/test.parquet",
    })

Use `evaluation` to pick a checkpoint during training, and `test` once at the end.
"""

import argparse
import hashlib
import json
import re
import unicodedata
from collections.abc import Callable
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from datasets import concatenate_datasets, load_dataset
from datasketch import MinHash, MinHashLSH

SAFE = 0
INJECTION = 1
HARMFUL = 2
LABEL_NAMES = {SAFE: "SAFE", INJECTION: "INJECTION", HARMFUL: "HARMFUL"}
COLUMNS = [
    "text",
    "label",
    "source",
    "subsource",
    "attack_type",
    "source_harmful",
]
SPLITS = ("train", "evaluation", "test")

DEFAULT_OUTPUT = Path(__file__).parent / "data" / "system1_prompt_injection"
CURATED_FILE = "system1_benign_security.txt"
NUM_PERM = 128
# SPML and TensorTrust rows that are nothing but a fragment after unwrapping,
# like "Access code", only look like attacks next to their system prompt.
MIN_UNWRAPPED_CHARS = 12

ZERO_WIDTH = re.compile(r"[​-‍⁠﻿]")
LEADING_SYSTEM_BLOCK = re.compile(r"^\[System:.*?\]\s*\n", re.DOTALL)
TRAILING_SYSTEM_BLOCK = re.compile(r"\n\[System:.*\]\s*$", re.DOTALL)
BIAS_KEYWORDS = re.compile(r"password|hack|exploit|malware", re.IGNORECASE)


def load_all_splits(repo: str) -> pd.DataFrame:
    dataset = load_dataset(repo)
    return concatenate_datasets(list(dataset.values())).to_pandas()


def load_cgoosen() -> pd.DataFrame:
    df = load_all_splits("cgoosen/llm_guard_dataset")
    return pd.DataFrame(
        {
            "text": df["text"],
            "label": df["label"],
            "subsource": "",
            "attack_type": df["label"].map(
                {SAFE: "benign", INJECTION: "injection"}
            ),
        }
    )


def load_deepset() -> pd.DataFrame:
    df = load_all_splits("deepset/prompt-injections")
    return pd.DataFrame(
        {
            "text": df["text"],
            "label": df["label"],
            "subsource": "",
            "attack_type": df["label"].map(
                {SAFE: "benign", INJECTION: "injection"}
            ),
        }
    )


def load_curated() -> pd.DataFrame:
    """Harmless prompts that use the vocabulary attacks rely on, like "password".

    Nearly every source prompt with these words is an attack, so without this
    file a model can score well by treating the words themselves as the signal.
    """
    lines = (
        (Path(__file__).parent / CURATED_FILE).read_text("utf-8").splitlines()
    )
    return pd.DataFrame(
        {
            "text": [line for line in lines if line.strip()],
            "label": SAFE,
            "subsource": "",
            "attack_type": "curated_benign",
        }
    )


def load_rogue() -> pd.DataFrame:
    df = load_all_splits("rogue-security/prompt-injections-benchmark")
    return pd.DataFrame(
        {
            "text": df["text"],
            "label": df["label"].map({"benign": SAFE, "jailbreak": INJECTION}),
            "subsource": "",
            "attack_type": df["label"],
        }
    )


def load_notinject() -> pd.DataFrame:
    """Harmless prompts containing words that often appear in attacks."""
    df = load_all_splits("leolee99/NotInject")
    return pd.DataFrame(
        {
            "text": df["prompt"],
            "label": SAFE,
            "subsource": df["category"],
            "attack_type": "trigger_word_benign",
        }
    )


def unwrap_system_blocks(text: str) -> str:
    """Keep only the attacker's input from a `[System: ...]` wrapped prompt."""
    return TRAILING_SYSTEM_BLOCK.sub("", LEADING_SYSTEM_BLOCK.sub("", text))


def load_htb() -> pd.DataFrame:
    """Map the HTB rows onto what they say about prompt manipulation.

    `is_dangerous` is 1 on every row, so it can't be the label. Rows with
    prompt_adversarial=0 are plain harmful requests rather than attacks on the
    prompt, so they get their own class. main() keeps them only for subsources
    named in --harmful-subsources. Adversarial rows with prompt_harmful=0 are
    harmless prompts written to look like jailbreaks, which makes them hard
    negatives. Only SPML and TensorTrust carry a system wrapper, and only on
    positives, so leaving it in would hand the model the label.
    """
    df = load_all_splits("htb-ac-1424625/llm-prompt-injection-filtered-cyber")
    df = df.copy()

    plain_harmful = df["prompt_adversarial"] == 0
    hard_negative = (
        ~plain_harmful
        & (df["prompt_harmful"] == 0)
        & (df["category"] == "benign")
    )
    wrapped = df["source"].isin(["SPML", "TensorTrust"])
    df.loc[wrapped, "prompt"] = df.loc[wrapped, "prompt"].map(
        unwrap_system_blocks
    )
    too_short = wrapped & (
        df["prompt"].str.strip().str.len() < MIN_UNWRAPPED_CHARS
    )

    out = pd.DataFrame(
        {
            "text": df["prompt"],
            "label": np.select(
                [plain_harmful, hard_negative], [HARMFUL, SAFE], INJECTION
            ),
            "subsource": df["source"],
            "attack_type": np.select(
                [plain_harmful, hard_negative],
                ["harmful_behavior", "adversarial_benign"],
                df["prompt_type"],
            ),
            "source_harmful": df["prompt_harmful"],
        }
    )
    return out[~too_short]


# Order sets precedence: when rows are duplicates, the earliest source is kept.
SOURCES: dict[str, tuple[str, Callable[[], pd.DataFrame]]] = {
    "cgoosen": ("cgoosen/llm_guard_dataset", load_cgoosen),
    "deepset": ("deepset/prompt-injections", load_deepset),
    "notinject": ("leolee99/NotInject", load_notinject),
    "curated": (CURATED_FILE, load_curated),
    "rogue": ("rogue-security/prompt-injections-benchmark", load_rogue),
    "htb": ("htb-ac-1424625/llm-prompt-injection-filtered-cyber", load_htb),
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = ZERO_WIDTH.sub("", text)
    return " ".join(text.split()).casefold()


def dedup_key(normalized: str) -> str:
    """Ignore punctuation and spacing, unless the text is nothing but those."""
    return re.sub(r"\W+", "", normalized) or normalized


def shingles(normalized: str) -> set[bytes]:
    """Word 3-grams, or character 4-grams for short or unspaced text."""
    words = re.findall(r"\w+", normalized)
    if len(words) >= 8:
        grams = {" ".join(words[i : i + 3]) for i in range(len(words) - 2)}
    else:
        grams = {
            normalized[i : i + 4] for i in range(max(1, len(normalized) - 3))
        }
    return {gram.encode("utf-8") for gram in grams}


def duplicate_stats(df: pd.DataFrame) -> dict:
    """Count duplicates inside each source and overlaps between each pair."""
    keys = {
        name: set(group["dedup_key"]) for name, group in df.groupby("source")
    }
    return {
        "within_source": {
            name: int(group["dedup_key"].duplicated().sum())
            for name, group in df.groupby("source")
        },
        "between_sources": {
            f"{a}&{b}": len(keys[a] & keys[b])
            for a, b in combinations(sorted(keys), 2)
        },
    }


def drop_exact_duplicates(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Keep the first row per dedup key, removing label conflicts entirely.

    Nothing says which source is right when the same text has both labels, so
    neither row is trusted. The conflicting rows are returned for auditing.
    """
    conflicted = df.groupby("dedup_key")["label"].transform("nunique") > 1
    conflicts = (
        df[conflicted].drop(columns=["key", "dedup_key"]).sort_values("text")
    )
    return df[~conflicted].drop_duplicates("dedup_key", keep="first"), conflicts


def cluster_near_duplicates(
    df: pd.DataFrame, threshold: float
) -> tuple[pd.DataFrame, dict]:
    """Assign rows to near-duplicate clusters and drop the redundant members.

    Rows only ever join a cluster leader, never another member, so one template
    can't chain unrelated prompts together. A cluster keeps one row per label:
    near-identical prompts with opposite labels are useful contrast pairs, and
    sharing a group_id keeps both in the same split.
    """
    lsh = MinHashLSH(threshold=threshold, num_perm=NUM_PERM)
    leaders: dict[int, MinHash] = {}
    cluster_labels: dict[int, set[int]] = {}
    group_ids: list[int] = []
    keep: list[bool] = []
    dropped_same_label = 0
    contrast_rows = 0

    for key, label in zip(df["key"], df["label"]):
        minhash = MinHash(num_perm=NUM_PERM, seed=1)
        minhash.update_batch(list(shingles(key)))

        scored = [(minhash.jaccard(leaders[c]), c) for c in lsh.query(minhash)]
        scored = [(score, c) for score, c in scored if score >= threshold]

        if not scored:
            group = len(leaders)
            leaders[group] = minhash
            cluster_labels[group] = {label}
            lsh.insert(group, minhash)
            group_ids.append(group)
            keep.append(True)
            continue

        group = max(scored, key=lambda item: (item[0], -item[1]))[1]
        group_ids.append(group)
        if label in cluster_labels[group]:
            keep.append(False)
            dropped_same_label += 1
        else:
            cluster_labels[group].add(label)
            keep.append(True)
            contrast_rows += 1

    out = df.assign(group_id=group_ids)[keep]
    return out, {
        "threshold": threshold,
        "near_duplicates_dropped": dropped_same_label,
        "opposite_label_rows_kept": contrast_rows,
    }


def cap_htb_subsources(
    df: pd.DataFrame, cap: int, seed: int
) -> tuple[pd.DataFrame, dict]:
    """Stop one synthetic HTB subsource from defining what an attack looks like."""
    is_htb = df["source"] == "htb"
    capped = (
        df[is_htb]
        .groupby(["subsource", "label"], group_keys=False)
        .sample(frac=1.0, random_state=seed)
        .groupby(["subsource", "label"], group_keys=False)
        .head(cap)
    )
    before = df[is_htb].groupby("subsource").size()
    after = capped.groupby("subsource").size()
    removed = (before - after.reindex(before.index, fill_value=0)).astype(int)
    return (
        pd.concat([df[~is_htb], capped]).sort_index(),
        {"cap": cap, "removed": removed[removed > 0].to_dict()},
    )


def assign_splits(
    df: pd.DataFrame, evaluation: float, test: float, seed: int
) -> pd.Series:
    """Assign whole clusters to splits, stratified by source and label."""
    rng = np.random.default_rng(seed)
    leaders = df.drop_duplicates("group_id")
    assignment: dict[int, str] = {}

    for _, stratum in leaders.groupby(
        ["source", "subsource", "label"], sort=True
    ):
        groups = rng.permutation(stratum["group_id"].to_numpy())
        n_test = round(len(groups) * test)
        n_evaluation = round(len(groups) * evaluation)
        n_train = len(groups) - n_evaluation - n_test
        for position, group in enumerate(groups):
            if position < n_train:
                assignment[int(group)] = "train"
            elif position < n_train + n_evaluation:
                assignment[int(group)] = "evaluation"
            else:
                assignment[int(group)] = "test"

    return df["group_id"].map(assignment)


def verify_splits(df: pd.DataFrame) -> None:
    """Fail the build if a text or a cluster appears in more than one split."""
    for column in ("dedup_key", "group_id"):
        spread = df.groupby(column)["split"].nunique()
        if (spread > 1).any():
            raise RuntimeError(
                f"{(spread > 1).sum()} {column} values span several splits"
            )
    if df["dedup_key"].duplicated().any():
        raise RuntimeError("Exact duplicates survived deduplication")


def label_signals(df: pd.DataFrame) -> dict:
    """Surface features that track the label, which a model may learn instead."""
    grouped = df.groupby("label")["text"]
    return {
        "bias_keyword_rate": grouped.apply(
            lambda s: round(s.str.contains(BIAS_KEYWORDS).mean(), 4)
        ).to_dict(),
        "all_lowercase_rate": grouped.apply(
            lambda s: round((s == s.str.lower()).mean(), 4)
        ).to_dict(),
        "system_wrapper_rate": grouped.apply(
            lambda s: round(s.str.startswith("[System").mean(), 4)
        ).to_dict(),
        "median_chars": grouped.apply(
            lambda s: float(s.str.len().median())
        ).to_dict(),
    }


def split_summary(df: pd.DataFrame) -> dict:
    summary = {}
    for split in SPLITS:
        rows = df[df["split"] == split]
        summary[split] = {
            "rows": len(rows),
            "labels": rows["label_name"].value_counts().to_dict(),
            "sources": rows["source"].value_counts().to_dict(),
        }
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--exclude", nargs="*", default=[], choices=sorted(SOURCES)
    )
    parser.add_argument(
        "--exclude-htb-subsources",
        nargs="*",
        default=[],
        help="Upstream sources to remove from the HTB dataset, like WildGuardMix.",
    )
    parser.add_argument(
        "--harmful-subsources",
        nargs="*",
        default=[],
        help="HTB upstream sources whose plain harmful requests to keep.",
    )
    parser.add_argument("--evaluation-size", type=float, default=0.1)
    parser.add_argument("--test-size", type=float, default=0.1)
    parser.add_argument("--near-dup-threshold", type=float, default=0.8)
    parser.add_argument("--max-chars", type=int, default=8000)
    parser.add_argument(
        "--htb-subsource-cap",
        type=int,
        default=3000,
        help="Maximum rows per label for each upstream source inside the HTB dataset.",
    )
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.evaluation_size + args.test_size >= 1:
        raise SystemExit(
            "--evaluation-size and --test-size must leave rows for train"
        )

    frames = []
    for name, (repo, loader) in SOURCES.items():
        if name in args.exclude:
            continue
        print(f"Loading {repo}")
        frames.append(loader().assign(source=name))
    df = pd.concat(frames, ignore_index=True)
    excluded_upstream = (df["source"] == "htb") & df["subsource"].isin(
        args.exclude_htb_subsources
    )
    missing = set(args.exclude_htb_subsources + args.harmful_subsources) - set(
        df.loc[df["source"] == "htb", "subsource"]
    )
    if missing:
        raise SystemExit(f"Unknown HTB subsources: {sorted(missing)}")
    unwanted_harmful = (df["label"] == HARMFUL) & ~df["subsource"].isin(
        args.harmful_subsources
    )
    df = df[~excluded_upstream & ~unwanted_harmful].copy()
    loaded = df["source"].value_counts().to_dict()

    df = df.dropna(subset=["text", "label"])
    df["text"] = df["text"].str.strip()
    df["label"] = df["label"].astype(int)
    df["key"] = df["text"].map(normalize)
    df["dedup_key"] = df["key"].map(dedup_key)
    too_long = df["text"].str.len() > args.max_chars
    empty = df["key"] == ""
    filtered = {"too_long": int(too_long.sum()), "empty": int(empty.sum())}
    df = df[~too_long & ~empty]

    duplicates = duplicate_stats(df)
    df, conflicts = drop_exact_duplicates(df)
    print(
        f"{len(df)} rows after exact dedup, {len(conflicts)} conflicting rows removed"
    )

    print("Clustering near-duplicates")
    df, near_duplicates = cluster_near_duplicates(df, args.near_dup_threshold)
    df, cap = cap_htb_subsources(df, args.htb_subsource_cap, args.seed)

    df["split"] = assign_splits(
        df, args.evaluation_size, args.test_size, args.seed
    )
    df["label_name"] = df["label"].map(LABEL_NAMES)
    verify_splits(df)

    args.output.mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        rows = df[df["split"] == split].sample(frac=1.0, random_state=args.seed)
        rows[COLUMNS + ["label_name", "group_id"]].to_parquet(
            args.output / f"{split}.parquet", index=False
        )
    conflicts.to_json(
        args.output / "label_conflicts.jsonl",
        orient="records",
        lines=True,
        force_ascii=False,
    )

    report = {
        "source_repos": {
            name: repo
            for name, (repo, _) in SOURCES.items()
            if name not in args.exclude
        },
        "excluded_htb_subsources": sorted(args.exclude_htb_subsources),
        "seed": args.seed,
        "rows_loaded": loaded,
        "filtered": filtered,
        "duplicates": {
            **duplicates,
            "label_conflict_rows_removed": len(conflicts),
            "near": near_duplicates,
        },
        "htb_subsource_cap": cap,
        "final_rows": len(df),
        "splits": split_summary(df),
        "label_signals": label_signals(df),
        "text_sha256": hashlib.sha256(
            "\n".join(sorted(df["text"])).encode("utf-8")
        ).hexdigest(),
    }
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(report["splits"], indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
