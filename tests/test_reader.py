"""
test_reader.py

Tests for reader.py -- uses a mocked DataHubGraph client.
"""
from unittest.mock import MagicMock

from datahub.metadata.schema_classes import (
    OwnershipClass,
    OwnerClass,
    OwnershipTypeClass,
    DatasetPropertiesClass,
)
from rules_engine.reader import get_dataset_info


def _urn():
    return "urn:li:dataset:(urn:li:dataPlatform:csv,customers,PROD)"


def test_dataset_with_owner_and_description():
    fake_graph = MagicMock()
    ownership = OwnershipClass(
        owners=[OwnerClass(owner="urn:li:corpuser:alice", type=OwnershipTypeClass.DATAOWNER)]
    )
    properties = DatasetPropertiesClass(description="Customer data")

    def fake_get_aspect(entity_urn, aspect_type):
        if aspect_type == OwnershipClass:
            return ownership
        if aspect_type == DatasetPropertiesClass:
            return properties
        return None

    fake_graph.get_aspect.side_effect = fake_get_aspect

    info = get_dataset_info(_urn(), fake_graph)

    assert info.name == "customers"
    assert info.platform == "csv"
    assert info.has_owner is True
    assert info.has_description is True


def test_dataset_missing_owner_and_description():
    fake_graph = MagicMock()
    fake_graph.get_aspect.return_value = None

    info = get_dataset_info(_urn(), fake_graph)

    assert info.has_owner is False
    assert info.has_description is False


def test_dataset_with_owner_but_empty_owners_list():
    fake_graph = MagicMock()
    ownership = OwnershipClass(owners=[])

    def fake_get_aspect(entity_urn, aspect_type):
        if aspect_type == OwnershipClass:
            return ownership
        return None

    fake_graph.get_aspect.side_effect = fake_get_aspect

    info = get_dataset_info(_urn(), fake_graph)
    assert info.has_owner is False