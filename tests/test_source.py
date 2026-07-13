"""
test_source.py

Tests for source.py -- pure logic, no network involved.
"""
from ingestion.source import read_csv_source


def _write_csv(tmp_path, content: str):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(content)
    return str(csv_file)


def test_single_table_single_column(tmp_path):
    csv_content = (
        "table_name,description,owner,column_name,column_type\n"
        "users,User data,alice@x.com,id,string\n"
    )
    path = _write_csv(tmp_path, csv_content)
    tables = read_csv_source(path)
    assert len(tables) == 1
    assert tables[0].name == "users"
    assert tables[0].owner == "alice@x.com"
    assert len(tables[0].columns) == 1
    assert tables[0].columns[0].name == "id"


def test_multiple_columns_grouped_into_one_table(tmp_path):
    csv_content = (
        "table_name,description,owner,column_name,column_type\n"
        "users,User data,alice@x.com,id,string\n"
        "users,User data,alice@x.com,email,string\n"
        "users,User data,alice@x.com,age,int\n"
    )
    path = _write_csv(tmp_path, csv_content)
    tables = read_csv_source(path)
    assert len(tables) == 1
    assert len(tables[0].columns) == 3
    column_names = [c.name for c in tables[0].columns]
    assert column_names == ["id", "email", "age"]


def test_multiple_tables_stay_separate(tmp_path):
    csv_content = (
        "table_name,description,owner,column_name,column_type\n"
        "users,User data,alice@x.com,id,string\n"
        "orders,Order data,bob@x.com,order_id,string\n"
    )
    path = _write_csv(tmp_path, csv_content)
    tables = read_csv_source(path)
    assert len(tables) == 2
    names = {t.name for t in tables}
    assert names == {"users", "orders"}


def test_missing_file_raises_error():
    try:
        read_csv_source("this/path/does/not/exist.csv")
        assert False, "Expected FileNotFoundError to be raised"
    except FileNotFoundError:
        pass