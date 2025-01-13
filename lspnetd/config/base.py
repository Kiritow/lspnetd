import sqlite3
from contextlib import contextmanager
from typing import Any, Sequence, Optional

class BaseSQLiteDB:
    def __init__(self, filename: str) -> None:
        # python 3.12 adds autocommit= parameter. before that we need to use isolation_level.
        # so we use BEGIN DEFERRED to start a transaction and commit/rollback in __exit__
        self.conn = sqlite3.connect(filename)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._flag_commit = True

    def __enter__(self):
        if not self._flag_commit:
            raise RuntimeError('nested with statement is not allowed')

        self._flag_commit = False
        self.cursor.execute("BEGIN DEFERRED")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb): # type: ignore
        if exc_type is None and exc_val is None and exc_tb is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self._flag_commit = True

    @contextmanager
    def _inner_enter(self):
        if self._flag_commit:
            # out most with statement
            with self:
                yield self
        else:
            # inner with statement
            yield self

    # sqlite3.Row supports indexing via idx or key.
    # To convert it to pure dict, use dict(row).
    def query(self, sql: str, params: Sequence[Any] = ()) -> list[sqlite3.Row]:
        with self._inner_enter():
            self.cursor.execute(sql, params)
            return self.cursor.fetchall()

    def queryone(self, sql: str, params: Sequence[Any] = ()) -> Optional[sqlite3.Row]:
        with self._inner_enter():
            self.cursor.execute(sql, params)
            return self.cursor.fetchone()

    def execute(self, sql: str, params: Sequence[Any] = ()) -> int:
        with self._inner_enter():
            self.cursor.execute(sql, params)
            return self.cursor.rowcount

    def insert_into(self, table_name: str, sql_fields: dict[str, Any], *, ignore: bool=False):
        table_struct = sorted(sql_fields.keys())
        sql = "insert into {}({}) values ({})".format(table_name, ','.join(table_struct), ','.join(["?"] * len(table_struct)))
        if ignore:
            # insert or ignore will not raise error even if constraints are violated. Use on conflict instead.
            sql += " on conflict do nothing"
        return self.execute(sql, [sql_fields[k] for k in table_struct])

    def replace_into(self, table_name: str, sql_fields: dict[str, Any]):
        table_struct = sorted(sql_fields.keys())
        return self.execute("replace into {}({}) values ({})".format(
            table_name,
            ','.join(table_struct),
            ','.join(["?"] * len(table_struct))
        ), [sql_fields[k] for k in table_struct])
