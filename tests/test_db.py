# tests/test_database.py
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.db import engine


def test_connection_to_database():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
    except SQLAlchemyError as e:
        assert False, f"Database connection failed: {e}"
