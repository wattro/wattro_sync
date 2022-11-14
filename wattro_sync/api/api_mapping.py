from dataclasses import dataclass
from typing import Literal, Type

from .sqlite_api import SQLiteSyncInfo, SQLiteApi


@dataclass
class ApiStructure:
    connection_info: type[SQLiteSyncInfo]
    api: type[SQLiteApi]


ApiNameToStructureMapping = {
    # "TopKontor": None,
    # "Mosaik": None,
    "Benning": ApiStructure(SQLiteSyncInfo, SQLiteApi),
    "SQLite": ApiStructure(SQLiteSyncInfo, SQLiteApi),
}
