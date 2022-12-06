from dataclasses import dataclass

from .mosaik_api import MosaikApi, MosaikSyncInfo
from .sqlite_api import SQLiteSyncInfo, SQLiteApi
from .src_cli import SrcCli, SyncInfo
from .topkontor_api import TopKontorSyncInfo, TopKontorApi


@dataclass
class ApiStructure:
    connection_info: type[SyncInfo]
    api: type[SrcCli]


ApiNameToStructureMapping: dict[str, ApiStructure] = {
    "Mosaik": ApiStructure(MosaikSyncInfo, MosaikApi),
    "TopKontor": ApiStructure(TopKontorSyncInfo, TopKontorApi),
    "Benning": ApiStructure(SQLiteSyncInfo, SQLiteApi),
    "SQLite": ApiStructure(SQLiteSyncInfo, SQLiteApi),
}
