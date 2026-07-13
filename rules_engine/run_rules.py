"""
run_rules.py

The command-line entry point for Part 2. Ties together:
  ingestion/source.py  -> gets the list of datasets to check (reusing
                          the same CSV Part 1 ingested)
  rule_loader.py        -> reads governance rules from YAML
  reader.py              -> queries DataHub for each dataset's real facts
                          (skipped in dry-run)
  evaluator.py           -> decides pass/fail per rule per dataset
  tagger.py              -> applies the resulting tags

Usage:
    python -m rules_engine.run_rules --dry-run
    python -m rules_engine.run_rules --gms-server http://localhost:8080
"""
import argparse
import logging
import sys

from ingestion.source import read_csv_source
from ingestion.mapper import build_urn
from rules_engine.rule_loader import load_rules
from rules_engine.evaluator import evaluate_rule, DatasetInfo
from rules_engine.tagger import TagApplier
from rules_engine.reader import build_graph_client, get_dataset_info

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def _dataset_info_from_csv(table) -> DatasetInfo:
    return DatasetInfo(
        name=table.name,
        platform="csv",
        has_owner=bool(table.owner),
        has_description=bool(table.description),
    )


def main():
    parser = argparse.ArgumentParser(description="Evaluate governance rules against DataHub datasets")
    parser.add_argument("--csv", default="data/sample.csv", help="CSV listing datasets to check")
    parser.add_argument("--rules", default="rules_engine/config/rules.yaml", help="Path to rules YAML")
    parser.add_argument("--gms-server", default="http://localhost:8080", help="DataHub GMS server address")
    parser.add_argument("--dry-run", action="store_true", help="Skip querying/tagging DataHub, just log")
    args = parser.parse_args()

    logger.info("Loading rules from: %s", args.rules)
    rules = load_rules(args.rules)
    logger.info("Loaded %d rule(s)", len(rules))

    logger.info("Reading dataset list from: %s", args.csv)
    try:
        tables = read_csv_source(args.csv)
    except FileNotFoundError:
        logger.error("CSV file not found: %s", args.csv)
        sys.exit(1)
    logger.info("Found %d dataset(s) to check", len(tables))

    graph = None if args.dry_run else build_graph_client(args.gms_server)
    tagger = TagApplier(gms_server=args.gms_server, dry_run=args.dry_run)

    total_checks = 0
    total_tagged = 0
    total_failed = 0

    for table in tables:
        urn = build_urn(table)

        if args.dry_run:
            dataset_info = _dataset_info_from_csv(table)
        else:
            dataset_info = get_dataset_info(urn, graph)

        for rule in rules:
            total_checks += 1
            actions = evaluate_rule(rule, dataset_info)

            if actions is None:
                continue

            success = tagger.apply_actions(urn, actions)
            if success:
                total_tagged += 1
            else:
                total_failed += 1

    logger.info(
        "Done. %d rule check(s) run, %d tag action(s) applied, %d failed.",
        total_checks,
        total_tagged,
        total_failed,
    )

    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()