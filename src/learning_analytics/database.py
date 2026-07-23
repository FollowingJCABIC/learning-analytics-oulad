from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pandas as pd
import psycopg

from learning_analytics.config import Settings


@contextmanager
def connect(settings: Settings) -> Iterator[psycopg.Connection[Any]]:
    connection = psycopg.connect(settings.database_url)
    try:
        yield connection
    finally:
        connection.close()


def read_query(settings: Settings, query: str, params: tuple[Any, ...] = ()) -> pd.DataFrame:
    with connect(settings) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            columns = [column.name for column in cursor.description or []]
            return pd.DataFrame(cursor.fetchall(), columns=columns)
