from __future__ import annotations

import dataclasses
import sqlite3

from .src_cli import SrcCli, DBRes, CollectionInfo, SyncInfo


class SQLiteSyncInfo(SyncInfo):
    db_path: str
    collection_info: CollectionInfo

    def __init__(self, db_path: str, collection_info: CollectionInfo):
        self.db_path = db_path
        self.collection_info = collection_info

    def asdict(self) -> dict:
        return {
            "db_path": str(self.db_path),
            "collection_info": dataclasses.asdict(self.collection_info),
        }

    @classmethod
    def from_dict(cls, info: dict) -> SQLiteSyncInfo:
        return cls(
            db_path=info["db_path"],
            collection_info=CollectionInfo(**info["collection_info"]),
        )


class SQLiteApi(SrcCli):
    def __init__(self, sync_info: SQLiteSyncInfo):
        self.db_path = sync_info.db_path
        self.collection_info = sync_info.collection_info

    @classmethod
    def get_fields(
        cls, connection_info: str, collection: str
    ) -> tuple[list[str], dict[str, list]]:
        fake_api = cls(SQLiteSyncInfo(connection_info, CollectionInfo.empty()))
        meta_info = fake_api._exec(f"PRAGMA table_info({collection})")
        field_names = sorted(list([str(x["name"]) for x in meta_info]))

        db_res = fake_api._exec(f"SELECT * FROM {collection} LIMIT 50")
        transposed_rows = list(map(list, zip(*db_res.rows)))
        sample_values = {
            field: val for field, val in zip(db_res.description, transposed_rows)
        }
        return field_names, sample_values

    @classmethod
    def get_collections(cls, connection_info: str) -> list[str]:
        """
        get_collections('/path/to/db')
        """
        fake_api = cls(
            SQLiteSyncInfo(
                db_path=connection_info, collection_info=CollectionInfo.empty()
            )
        )
        db_res = fake_api._exec(f"PRAGMA table_list")
        return sorted([x["name"] for x in db_res])

    def _exec(self, qry: str, params=None) -> DBRes:
        cnxn = sqlite3.connect(self.db_path)
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
