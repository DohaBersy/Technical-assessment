"""
test_mapper.py

Tests for mapper.py -- also pure logic, no mocking needed.
"""
from ingestion.source import TableRecord, ColumnInfo
from ingestion.mapper import (
    build_urn,
    build_properties_aspect,
    build_ownership_aspect,
    build_schema_aspect,
)


def _sample_table():
    return TableRecord(
        name="customers",
        description="Customer master data",
        owner="alice@company.com",
        columns=[
            ColumnInfo(name="customer_id", data_type="string"),
            ColumnInfo(name="signup_date", data_type="date"),
        ],
    )


def test_build_urn_format():
    table = _sample_table()
    urn = build_urn(table)
    assert urn == "urn:li:dataset:(urn:li:dataPlatform:csv,customers,PROD)"


def test_properties_aspect_has_description():
    table = _sample_table()
    props = build_properties_aspect(table)
    assert props.description == "Customer master data"


def test_ownership_aspect_maps_owner_correctly():
    table = _sample_table()
    ownership = build_ownership_aspect(table)
    assert len(ownership.owners) == 1
    assert ownership.owners[0].owner == "urn:li:corpuser:alice@company.com"


def test_schema_aspect_includes_all_columns():
    table = _sample_table()
    schema = build_schema_aspect(table)
    field_names = [f.fieldPath for f in schema.fields]
    assert field_names == ["customer_id", "signup_date"]


def test_schema_aspect_handles_unknown_type_gracefully():
    table = TableRecord(
        name="weird_table",
        description="test",
        owner="x@x.com",
        columns=[ColumnInfo(name="mystery_col", data_type="some_unknown_type")],
    )
    schema = build_schema_aspect(table)
    assert len(schema.fields) == 1
    assert schema.fields[0].fieldPath == "mystery_col"