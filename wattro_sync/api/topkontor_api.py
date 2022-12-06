from __future__ import annotations

from wattro_sync.api.odbc_api import OdbcSyncInfo, OdbcSrcCliAltSample


class TopKontorSyncInfo(OdbcSyncInfo):
    """branded OdbcSyncInfo"""


class TopKontorApi(OdbcSrcCliAltSample):
    @classmethod
    def get_collections(cls, connection_info: str) -> list[str]:
        raise NotImplementedError("Not implemented for TopKontor.")

    @classmethod
    def get_fields(
        cls, connection_info: str, collection: str
    ) -> tuple[list[str], dict[str, list]]:
        raise NotImplementedError("Not implemented for TopKontor.")
