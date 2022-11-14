from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal, NewType

from wattro_sync.api.sqlite_api import SQLiteSyncInfo

FieldMapping = NewType("FieldMapping", dict[str, dict[str, None | int | str]])


@dataclass
class ConnectionStructure:
    connection_type: Literal["SQLite"]
    sync_info: SQLiteSyncInfo
    field_mapping: FieldMapping
    encoding: str = "utf-8"


@dataclass
class WattroCfg:
    domain: str
    api_key: str


@dataclass
class MailCfg:
    api_key: str
    to_emails: str
    log_level: int = logging.WARNING
    form_email: str = "admin@wattro.de"


@dataclass
class SyncCfg:
    wattro_cfg: WattroCfg
    asset: None | ConnectionStructure
    project: None | ConnectionStructure
    mail_cfg: None | MailCfg


class ConfigDegenerated(Exception):
    """Config File exists but is not as expected"""
