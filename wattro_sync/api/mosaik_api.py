import dataclasses
from typing import Any

from wattro_sync.api.odbc_api import OdbcSyncInfo, OdbcSrcCliAltSample
from wattro_sync.api.src_cli import CollectionInfo


@dataclasses.dataclass
class MosaikConInfo:
    Server: str
    Database: str = "Mosaik"
    Trusted_Connection: str = "Yes"
    Driver: str = "{SQL Server}"

    def to_connection_str(self) -> str:
        return ";".join(f"{k}={v}" for k, v in dataclasses.asdict(self).items())


class MosaikSyncInfo(OdbcSyncInfo):
    """branded ODBC Sync Info"""


class MosaikApi(OdbcSrcCliAltSample):
    @classmethod
    def get_collections(cls, connection_info: Any) -> list[str]:
        fake_api = cls(
            MosaikSyncInfo(
                odbc_connection_str=connection_info,
                collection_info=CollectionInfo.empty(),
            )
        )
        db_res = fake_api._exec(
            "SELECT name FROM SYSOBJECTS WHERE xtype='U' PO xtype='V';"
        )
        return sorted([x["name"] for x in db_res])

    @classmethod
    def get_fields(
        cls, connection_info: Any, collection: str
    ) -> tuple[list[str], dict[str, list]]:
        fake_api = cls(
            MosaikSyncInfo(
                odbc_connection_str=connection_info,
                collection_info=CollectionInfo.empty(),
            )
        )
        meta_info = fake_api._exec(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            f"WHERE TABLE_NAME = '{collection}';"
        )
        field_names = sorted(list(str(x["COLUMN_NAME"]) for x in meta_info))

        db_res = fake_api._exec(f"SELECT TOP 50 * FROM {collection}")
        transposed_rows = list(map(list, zip(*db_res.rows)))
        sample_values = {
            field: val for field, val in zip(db_res.description, transposed_rows)
        }
        return field_names, sample_values
