"""
run_ingestion.py

Reads a CSV of table metadata and sends it to DataHub.

Usage:
    python -m ingestion.run_ingestion --dry-run
    python -m ingestion.run_ingestion --csv data/sample.csv --gms-server http://localhost:8080
"""
import argparse
import logging
import sys

from ingestion.source import read_csv_source
from ingestion.emitter import MetadataEmitter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    # Read what the user typed after the command, e.g. --dry-run
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/sample.csv")
    parser.add_argument("--gms-server", default="http://localhost:8080")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Step 1: read the CSV file into a list of tables
    logger.info("Reading source CSV: %s", args.csv)
    try:
        tables = read_csv_source(args.csv)
    except FileNotFoundError:
        logger.error("CSV file not found: %s", args.csv)
        sys.exit(1)

    logger.info("Found %d table(s) to ingest", len(tables))

    # Step 2: send each table to DataHub (or just log it, if --dry-run)
    emitter = MetadataEmitter(gms_server=args.gms_server, dry_run=args.dry_run)
    summary = emitter.emit_all(tables)

    # Step 3: report what happened
    logger.info("Done. %d succeeded, %d failed.", summary["succeeded"], summary["failed"])
    if summary["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()