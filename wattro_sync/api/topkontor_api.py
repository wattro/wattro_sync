from __future__ import annotations

import dataclasses

import pyodbc as pyodbc

from wattro_sync.api.src_cli import SrcCli, SyncInfo, CollectionInfo, DBRes


class TopKontorSyncInfo(SyncInfo):
    odbc_connection_str: str
    collection_info: CollectionInfo

    def __init__(self, odbc_connection_str: str, collection_info: CollectionInfo):
        self.odbc_connection_str = odbc_connection_str
        self.collection_info = collection_info

    @classmethod
    def from_dict(cls, info: dict) -> TopKontorSyncInfo:
        return cls(
            info["odbc_connection_str"], CollectionInfo(**info["collection_info"])
        )

    def asdict(self) -> dict:
        return {
            "odbc_connection_str": self.odbc_connection_str,
            "collection_info": dataclasses.asdict(self.collection_info),
        }


class TopKontorApi(SrcCli):
    def __init__(self, sync_info: TopKontorSyncInfo):
        self.collection_info = sync_info.collection_info
        self.obdc_connection_str = sync_info.odbc_connection_str

    def get_sample(self) -> DBRes:
        """use advantage db syntax
        https://devzone.advantagedatabase.com/dz/webhelp/Advantage11/index.html?devguide_sql_scripts.htm
        """
        qry = self._qry("").strip(";")
        sample_table = f"({qry}) as sample_table"
        return self._exec(f"SELECT TOP 1 * FROM {sample_table};")

    def _exec(self, qry: str, params=None) -> DBRes:
        cnxn = pyodbc.connect(self.obdc_connection_str)
        cursor = cnxn.cursor()
        if params is None:
            params = tuple()
        rows = cursor.execute(qry, params).fetchall()
        if not rows:
            res = DBRes([], [])
        else:
            res = DBRes([n[0] for n in cursor.description], rows)
        cnxn.close()
        return res

    @classmethod
    def get_collections(cls, connection_info: str) -> list[str]:
        raise NotImplementedError("Not implemented for TopKontor.")

    @classmethod
    def get_fields(
        cls, connection_info: str, collection: str
    ) -> tuple[list[str], dict[str, list]]:
        raise NotImplementedError("Not implemented for TopKontor.")
