"""
source.py

Reads the CSV data source and groups rows by table_name, so that
each "table" becomes one Python object with a list of its columns.

The CSV has one row PER COLUMN, so a table with 3 columns appears as
3 rows sharing the same table_name/description/owner. This module's
job is just to reassemble that back into a per-table shape.
"""
import csv
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class ColumnInfo:
    name: str
    data_type: str


@dataclass
class TableRecord:
    name: str
    description: str
    owner: str
    columns: List[ColumnInfo] = field(default_factory=list)


def read_csv_source(path: str) -> List[TableRecord]:
    """
    Reads the CSV at `path` and returns a list of TableRecord objects,
    one per unique table_name, each containing all of its columns.
    """
    tables: Dict[str, TableRecord] = {}

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            table_name = row["table_name"].strip()

            if table_name not in tables:
                tables[table_name] = TableRecord(
                    name=table_name,
                    description=row["description"].strip(),
                    owner=row["owner"].strip(),
                )

            tables[table_name].columns.append(
                ColumnInfo(
                    name=row["column_name"].strip(),
                    data_type=row["column_type"].strip(),
                )
            )

    return list(tables.values())