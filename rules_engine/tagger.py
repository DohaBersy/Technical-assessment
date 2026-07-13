"""
tagger.py

Applies the tags decided by evaluator.py to a dataset in DataHub.
"""
import logging
from typing import List

from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import GlobalTagsClass, TagAssociationClass

from rules_engine.rule_loader import Action

logger = logging.getLogger(__name__)


class TagApplier:
    def __init__(self, gms_server: str, dry_run: bool = False):
        self.dry_run = dry_run
        if dry_run:
            self._emitter = None
        else:
            self._emitter = DatahubRestEmitter(gms_server=gms_server)

    def apply_actions(self, urn: str, actions: List[Action]) -> bool:
        try:
            # Step 1: go through every action, and collect only the
            # tag names from the ones that are "add_tag" actions.
            tag_urns = []
            for action in actions:
                if action.action == "add_tag":
                    tag_urns.append(action.tag)

            # If we found no tags to add, there's nothing to do.
            if len(tag_urns) == 0:
                return True

            # Step 2: wrap each tag string into the object DataHub expects.
            tag_associations = []
            for tag in tag_urns:
                tag_associations.append(TagAssociationClass(tag=tag))

            # Step 3: bundle all those wrapped tags into one aspect.
            tags_aspect = GlobalTagsClass(tags=tag_associations)

            # Step 4: attach that aspect to the dataset's URN.
            mcp = MetadataChangeProposalWrapper(entityUrn=urn, aspect=tags_aspect)

            # Step 5: send it for real, or just log it in dry-run mode.
            if self.dry_run:
                logger.info("[DRY_RUN] Would apply tags %s to %s", tag_urns, urn)
            else:
                self._emitter.emit(mcp)
                logger.info("Applied tags %s to %s", tag_urns, urn)

            return True

        except Exception as e:
            logger.error("Failed to apply tags to '%s': %s", urn, e)
            return False