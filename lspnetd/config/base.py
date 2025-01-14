import sqlite3
from contextlib import contextmanager
import sys
from typing import Any, Sequence, Optional

class BaseSQLiteDB:
    def __init__(self, filename: str, debug: bool=False) -> None:
        # python 3.12 adds autocommit= parameter. before that we need to use isolation_level.
        # we just tell python to stop messing with transactions, and "leave the underlying SQLite library in autocommit mode"

        if sys.version_info >= (3, 12):
            self.conn = sqlite3.connect(filename, autocommit=True, isolation_level=None)
        else:
            self.conn = sqlite3.connect(filename, isolation_level=None)

        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._debug = debug
    
    def _wrap_execute(self, sql: str, params: Sequence[Any] = ()):
        if self._debug:
            print(sql, params)
        self.cursor.execute(sql, params)

    def __enter__(self):
        if self.conn.in_transaction:
            raise RuntimeError('nested with statement is not allowed')

        self._wrap_execute("BEGIN DEFERRED")
        assert self.conn.in_transaction

        return self

    def __exit__(self, exc_type, exc_val, exc_tb): # type: ignore
        if exc_type is None and exc_val is None and exc_tb is None:
            self._wrap_execute("COMMIT")
            assert not self.conn.in_transaction
        else:
            self._wrap_execute("ROLLBACK")
            assert not self.conn.in_transaction

    @contextmanager
    def immediate(self):
        if self.conn.in_transaction:
            raise RuntimeError('nested with statement is not allowed')

        self._wrap_execute("BEGIN IMMEDIATE")
        assert self.conn.in_transaction

        try:
            yield self
            self._wrap_execute("COMMIT")
            assert not self.conn.in_transaction
        except Exception:
            self._wrap_execute("ROLLBACK")
            assert not self.conn.in_transaction
            raise

    @contextmanager
    def exclusive(self):
        if self.conn.in_transaction:
            raise RuntimeError('nested with statement is not allowed')

        self._wrap_execute("BEGIN EXCLUSIVE")
        assert self.conn.in_transaction

        try:
            yield self
            self._wrap_execute("COMMIT")
            assert not self.conn.in_transaction
        except Exception:
            self._wrap_execute("ROLLBACK")
            assert not self.conn.in_transaction
            raise

    @contextmanager
    def _inner_enter(self):
        if not self.conn.in_transaction:
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
            self._wrap_execute(sql, params)
            return self.cursor.fetchall()

    def queryone(self, sql: str, params: Sequence[Any] = ()) -> Optional[sqlite3.Row]:
        with self._inner_enter():
            self._wrap_execute(sql, params)
            return self.cursor.fetchone()

    def execute(self, sql: str, params: Sequence[Any] = ()) -> int:
        with self._inner_enter():
            self._wrap_execute(sql, params)
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
