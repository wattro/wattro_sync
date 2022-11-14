from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from wattro_sync.api.sqlite_api import SQLiteSyncInfo


@dataclass
class ConnectionStructure:
    connection_type: Literal['SQLite']
    connection_info: SQLiteSyncInfo


@dataclass
class WattroCfg:
    domain: str
    api_key: str


@dataclass
class SyncCfg:
    wattro_cfg: WattroCfg
    asset: None | ConnectionStructure
