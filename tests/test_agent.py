import pytest

from backend.database import execute_query
from backend.sql_validator import validate_sql


def test_select_is_allowed():
    query = "SELECT * FROM users"
    assert validate_sql(query) == query


def test_insert_is_rejected():
    with pytest.raises(ValueError):
        execute_query(
            "INSERT INTO users (name) VALUES ('Test')"
        )


def test_update_is_rejected():
    with pytest.raises(ValueError):
        execute_query(
            "UPDATE users SET city = 'Pune'"
        )


def test_delete_is_rejected():
    with pytest.raises(ValueError):
        execute_query(
            "DELETE FROM users"
        )


def test_drop_is_rejected():
    with pytest.raises(ValueError):
        execute_query(
            "DROP TABLE users"
        )


def test_multiple_statements_are_rejected():
    with pytest.raises(ValueError):
        validate_sql(
            "SELECT * FROM users; DELETE FROM users;"
        )