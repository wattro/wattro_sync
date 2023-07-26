from __future__ import annotations

import dataclasses
from abc import ABC

import pyodbc as pyodbc

from wattro_sync.api.src_cli import SyncInfo, CollectionInfo, SrcCli, DBRes


class OdbcSyncInfo(SyncInfo):
    odbc_connection_str: str
    collection_info: CollectionInfo

    def __init__(self, odbc_connection_str: str, collection_info: CollectionInfo):
        self.odbc_connection_str = odbc_connection_str
        self.collection_info = collection_info

    @classmethod
    def from_dict(cls, info: dict) -> OdbcSyncInfo:
        return cls(
            info["odbc_connection_str"], CollectionInfo(**info["collection_info"])
        )

    def asdict(self) -> dict:
        return {
            "odbc_connection_str": self.odbc_connection_str,
            "collection_info": dataclasses.asdict(self.collection_info),
        }


class OdbcSrcCli(SrcCli, ABC):
    def __init__(self, sync_info: OdbcSyncInfo):
        self.collection_info = sync_info.collection_info
        self.odbc_connection_str = sync_info.odbc_connection_str

    def _exec(self, qry: str, params=None) -> DBRes:
        try:
            cnxn = pyodbc.connect(self.odbc_connection_str)
        except Exception as err:
            raise ConnectionError(
                f"Failed to connect using {self.odbc_connection_str!r}"
            ) from err
        try:
            cursor = cnxn.cursor()
            if params is None:
                params = tuple()
            rows = cursor.execute(qry, params).fetchall()
            if not rows:
                res = DBRes([], [])
            else:
                res = DBRes([n[0] for n in cursor.description], rows)
        except Exception as err:
            raise RuntimeError(
                f"Failed to execute {qry = !r} with {params = !r}"
            ) from err
        finally:
            cnxn.close()
        return res


class OdbcSrcCliAltSample(OdbcSrcCli, ABC):
    def get_sample(self) -> DBRes:
        """For Sources that do not implement the LIMIT statement but the TOP statement."""
        qry = self._qry("").strip(";")
        sample_table = f"({qry}) as sample_table"
        return self._exec(f"SELECT TOP 1 * FROM {sample_table};")
