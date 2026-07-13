"""
reader.py

Queries DataHub to build a DatasetInfo object for a given URN.
Uses DataHubGraph (a read+write client), unlike emitter.py/tagger.py
which only ever WRITE via DatahubRestEmitter.
"""
import logging

from datahub.ingestion.graph.client import DataHubGraph, DatahubClientConfig
from datahub.metadata.schema_classes import OwnershipClass, DatasetPropertiesClass
from datahub.metadata.urns import DatasetUrn

from rules_engine.evaluator import DatasetInfo

logger = logging.getLogger(__name__)


def build_graph_client(gms_server: str) -> DataHubGraph:
    """Creates a DataHubGraph client connected to the given server."""
    return DataHubGraph(DatahubClientConfig(server=gms_server))


def get_dataset_info(urn: str, graph: DataHubGraph) -> DatasetInfo:
    """
    Queries DataHub for the ownership and description aspects of
    the dataset identified by `urn`.
    """
    parsed = DatasetUrn.from_string(urn)
    platform = parsed.get_data_platform_urn().platform_name
    name =parsed.name

    ownership = graph.get_aspect(entity_urn=urn, aspect_type=OwnershipClass)
    has_owner = ownership is not None and len(ownership.owners) > 0

    properties = graph.get_aspect(entity_urn=urn, aspect_type=DatasetPropertiesClass)
    has_description = properties is not None and bool(properties.description)

    return DatasetInfo(
        name=name,
        platform=platform,
        has_owner=has_owner,
        has_description=has_description,
    )