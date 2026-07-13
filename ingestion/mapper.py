"""

Converts one TableRecord (from source.py) into the DataHub objects
we need to emit: a URN, plus three aspects (properties, ownership, schema).


"""
from datahub.emitter.mce_builder import make_dataset_urn
from datahub.metadata.schema_classes import (
    DatasetPropertiesClass,
    OwnershipClass,
    OwnerClass,
    OwnershipTypeClass,
    SchemaMetadataClass,
    SchemaFieldClass,
    SchemaFieldDataTypeClass,
    StringTypeClass,
    NumberTypeClass,
    DateTypeClass,
    BooleanTypeClass,
)

from ingestion.source import TableRecord

PLATFORM = "csv"
ENV = "PROD"

# Maps the plain-text type strings in our CSV (e.g. "string", "date")
# to the DataHub SDK's typed classes. This is how we handle different
# column types without hardcoding "if type == string" everywhere.
_TYPE_MAP = {
    "string": StringTypeClass,
    "double": NumberTypeClass,
    "int": NumberTypeClass,
    "float": NumberTypeClass,
    "date": DateTypeClass,
    "boolean": BooleanTypeClass,
}


def build_urn(table: TableRecord) -> str:
    """Builds the URN (unique address) for a table."""
    return make_dataset_urn(platform=PLATFORM, name=table.name, env=ENV)


def build_properties_aspect(table: TableRecord) -> DatasetPropertiesClass:
    """Builds the 'description' aspect."""
    return DatasetPropertiesClass(description=table.description)


def build_ownership_aspect(table: TableRecord) -> OwnershipClass:
    """Builds the 'who owns this' aspect."""
    owner_urn = f"urn:li:corpuser:{table.owner}"
    return OwnershipClass(
        owners=[OwnerClass(owner=owner_urn, type=OwnershipTypeClass.DATAOWNER)]
    )


def build_schema_aspect(table: TableRecord) -> SchemaMetadataClass:
    """Builds the 'columns and types' aspect."""
    fields = []
    for col in table.columns:
        type_class = _TYPE_MAP.get(col.data_type.lower(), StringTypeClass)
        fields.append(
            SchemaFieldClass(
                fieldPath=col.name,
                type=SchemaFieldDataTypeClass(type=type_class()),
                nativeDataType=col.data_type,
            )
        )

    return SchemaMetadataClass(
        schemaName=table.name,
        platform=f"urn:li:dataPlatform:{PLATFORM}",
        version=0,
        hash="",
        platformSchema=None,
        fields=fields,
    )