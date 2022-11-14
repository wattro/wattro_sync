from dataclasses import dataclass
from typing import Literal, Type

from .sqlite_api import SQLiteSyncInfo, SQLiteApi
from .src_cli import SrcCli, SyncInfo
from .topkontor_api import TopKontorSyncInfo, TopKontorApi


@dataclass
class ApiStructure:
    connection_info: type[SyncInfo]
    api: type[SrcCli]


ApiNameToStructureMapping: dict[str, ApiStructure] = {
    "TopKontor": ApiStructure(TopKontorSyncInfo, TopKontorApi),
    # "Mosaik": None,
    "Benning": ApiStructure(SQLiteSyncInfo, SQLiteApi),
    "SQLite": ApiStructure(SQLiteSyncInfo, SQLiteApi),
}
