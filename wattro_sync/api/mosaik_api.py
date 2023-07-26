import dataclasses
from typing import Any, Sequence

from wattro_sync.api.odbc_api import OdbcSyncInfo, OdbcSrcCliAltSample
from wattro_sync.api.src_cli import CollectionInfo, DBRes


@dataclasses.dataclass
class MosaikConInfo:
    Server: str
    Database: str
    Trusted_Connection: str = "Yes"
    Driver: str = "{SQL Server}"

    def to_connection_str(self) -> str:
        return ";".join(f"{k}={v}" for k, v in dataclasses.asdict(self).items())


class MosaikSyncInfo(OdbcSyncInfo):
    """branded ODBC Sync Info"""


class MosaikApi(OdbcSrcCliAltSample):
    MAX_SQL_TOKENS = 2_000

    @classmethod
    def get_collections(cls, connection_info: Any) -> list[str]:
        fake_api = cls(
            MosaikSyncInfo(
                odbc_connection_str=connection_info,
                collection_info=CollectionInfo.empty(),
            )
        )
        db_res = fake_api._exec(
            "SELECT name FROM SYSOBJECTS WHERE xtype='U' OR xtype='V';"
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

    def get_new(self, known_idents: Sequence[str]) -> DBRes:
        """
        Get all entries on the CollectionInfo collection that are not identified by `known_idents`
        This assumes that we are conntected to a view that sorts by changed date and is limited to the last 2k (or less)
        """
        return super().get_new(known_idents[: self.MAX_SQL_TOKENS])

    def get_old(self, known_idents: Sequence[str]) -> DBRes:
        """
        The DB is limited to 2k SQL tokens, so we have to limit known idents.
        This assumes that we are conntected to a view that sorts by changed date and is limited to the last 2k (or less)
        """
        return super().get_old(known_idents[: self.MAX_SQL_TOKENS])
