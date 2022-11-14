import dataclasses
import logging
import pathlib
import sqlite3

from .src_cli import SrcCli, DBRes, CollectionInfo


@dataclasses.dataclass
class SQLiteSyncInfo:
    db_path: pathlib.Path
    table_info: CollectionInfo


class SQLiteApi(SrcCli):
    def __init__(self, connection_info: SQLiteSyncInfo):
        self.connection_info = connection_info
        self.collection_info = connection_info.table_info

    def get_last(
        self,
        order_by_field: str = "",
        descending: bool = True,
        limit: int = 100,
    ) -> DBRes:
        if order_by_field == "":
            order_by_field = self.connection_info.table_info.fields[0]
        qry = f"{self._select()} ORDER BY ? {'DESC' if descending else 'ASC'} LIMIT ?;"
        return self._exec(qry, (order_by_field, limit))

    @classmethod
    def get_fields(
        cls, connection_info: pathlib.Path, collection: str
    ) -> tuple[list[str], dict[str, list]]:
        """
        get_fields('/path/to/db', 'TableToScan')
        returns a tuple of
        - list of field names (str)
        - list of a list of up to 10 sample values
        """
        fake_api = cls(SQLiteSyncInfo(connection_info, CollectionInfo.empty()))
        meta_info = fake_api._exec(f"PRAGMA table_info({collection})")
        field_names = sorted(list([str(x["name"]) for x in meta_info.iter_as_dict()]))

        db_res = fake_api._exec(f"SELECT * FROM {collection} LIMIT 50")
        transposed_rows = list(map(list, zip(*db_res.rows)))
        sample_values = {
            field: val for field, val in zip(db_res.description, transposed_rows)
        }
        return field_names, sample_values

    @classmethod
    def get_collections(cls, connection_info: pathlib.Path) -> list[str]:
        """
        get_collections('/path/to/db')
        """
        fake_api = cls(
            SQLiteSyncInfo(db_path=connection_info, table_info=CollectionInfo.empty())
        )
        db_res = fake_api._exec(f"PRAGMA table_list")
        return [x["name"] for x in db_res.iter_as_dict()]

    def get_new(self, known_idents: tuple) -> DBRes:
        qry = f"{self._select()} WHERE "
        qry += f"{self.collection_info.ident} NOT IN ({','.join(['?' for _ in known_idents])});"
        return self._exec(qry, known_idents)

    def _exec(self, qry: str, params=None) -> DBRes:
        cnxn = sqlite3.connect(self.connection_info.db_path)
        cursr = cnxn.cursor()
        if params is None:
            params = tuple()
        rows = cursr.execute(qry, params).fetchall()
        if not rows:
            res = DBRes([], [])
        else:
            res = DBRes([n[0] for n in cursr.description], rows)
        cnxn.close()
        return res

    def _select(
        self,
    ) -> str:
        return f"SELECT {','.join(self.collection_info.fields)} FROM {self.collection_info.collection_name}"

    @classmethod
    def get_healthy_connection(cls, connection_info: SQLiteSyncInfo):
        inst = cls(connection_info)
        succes = inst.get_last(limit=1)
        logging.info(
            "Successfully sampled %s in %s: %s",
            connection_info.table_info.collection_name,
            connection_info.db_path,
            succes,
        )
        return inst
