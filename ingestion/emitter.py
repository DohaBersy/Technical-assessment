"""
emitter.py

Wraps the DataHub REST emitter with Dry run mode (build everything, but don't actually send it) 
and error handling (one failed table shouldn't crash the whole run)
 
Idempotency isn't handled here explicitly -- it's a natural side effect
of always computing the same URN for the same table name (already handled in mapper.py).
DataHub treats re-emitting an aspect for an existing URN as an update,
not a duplicate insert.
"""
import logging
from typing import List

from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.emitter.mcp import MetadataChangeProposalWrapper

from ingestion.source import TableRecord
from ingestion.mapper import (
    build_urn,
    build_properties_aspect,
    build_ownership_aspect,
    build_schema_aspect,
)

logger = logging.getLogger(__name__)


class MetadataEmitter:
    def __init__(self, gms_server: str, dry_run: bool = False):
        self.dry_run = dry_run
        self._emitter = None if dry_run else DatahubRestEmitter(gms_server=gms_server)

    def emit_table(self, table: TableRecord) -> bool:
        """
        Emits all aspects for one table. Returns True on success,
        False if something went wrong (and logs the error instead
        of crashing the whole batch).
        """
        try:
            urn = build_urn(table)
            aspects = [
                build_properties_aspect(table),
                build_ownership_aspect(table),
                build_schema_aspect(table),
            ]

            for aspect in aspects:
                mcp = MetadataChangeProposalWrapper(entityUrn=urn, aspect=aspect)

                if self.dry_run:
                    logger.info(
                        "[DRY_RUN] Would emit %s aspect for %s",
                        type(aspect).__name__,
                        urn,
                    )
                else:
                    self._emitter.emit(mcp)

            logger.info("Successfully processed table: %s", table.name)
            return True

        except Exception as e:
            logger.error("Failed to emit table '%s': %s", table.name, e)
            return False

    def emit_all(self, tables: List[TableRecord]) -> dict:
        """
        Emits every table, tracking how many succeeded/failed.
        """
        succeeded = 0
        failed = 0
        for table in tables:
            if self.emit_table(table):
                succeeded += 1
            else:
                failed += 1

        return {"succeeded": succeeded, "failed": failed, "total": len(tables)}