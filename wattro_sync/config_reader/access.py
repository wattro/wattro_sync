from __future__ import annotations

import dataclasses
import logging
import pathlib

from .types import WattroCfg, ConnectionStructure, SyncCfg, MailCfg, ConfigDegenerated
from ..api.api_mapping import ApiNameToStructureMapping, ApiStructure
from ..api.src_cli import SyncInfo
from ..file_access.read_write import (
    CON_TYPE_KEY,
    CON_INFO_KEY,
    FIELD_MAP_KEY,
    cfg_update,
    write_path,
    get_or_create as get_or_create_fp,
    read_path,
)


def extract_wattro_cfg(cfg: dict) -> WattroCfg:
    """read_path wattro cfg form file"""
    if "wattro_cfg" not in cfg:
        raise ConfigDegenerated(f"'wattro_cfg' fehlt in {cfg}.")
    return WattroCfg(**cfg["wattro_cfg"])


def extract_src_cfg(cfg: dict, target: str) -> ConnectionStructure | None:
    """extract key from cfg and return structured data"""
    if target not in cfg:
        logging.info("Keine Konfiguration für %s. (Verfügbar: %s)", target, cfg.keys())
        return None
    cfg_data = cfg[target]
    con_type = cfg_data.get("connection_type", "")
    api_structure: ApiStructure = ApiNameToStructureMapping[con_type]

    con_info_data = cfg_data.get("connection_info", {})
    con_info = api_structure.connection_info.from_dict(con_info_data)
    field_mapping = cfg_data.get("field_mapping", {})
    encoding = cfg_data.get("encoding", "utf-8")

    return ConnectionStructure(
        connection_type=con_type,
        sync_info=con_info,
        field_mapping=field_mapping,
        encoding=encoding,
    )


def extract_mail_cfg(cfg: dict) -> MailCfg | None:
    """extract from dict and return structured data"""
    key = "mail"
    if key not in cfg:
        logging.info("Keine Konfiguration für E-Mail Benachrichtungen gefunden.")
        return None
    mail_cfg = cfg[key]
    return MailCfg(**mail_cfg)


def write_basic_connection(
    target: str, connection_type: str, sync_info: SyncInfo
) -> None:
    cfg_update(target, CON_TYPE_KEY, connection_type)
    cfg_update(target, CON_INFO_KEY, sync_info.asdict())


def write_field_mapping(target: str, field_mapping: dict) -> None:
    cfg_update(target, FIELD_MAP_KEY, field_mapping)


def _create_min_cfg(cfg_file: pathlib.Path) -> None:
    """Create Minimal Config."""
    print(f"Erzeuge Konfiguration in {cfg_file}. Bitte Informationen eingeben:")
    domain = input("Kunden Domain (Beispiel: `wattro`):\t")
    api_key = input("Api Key (Beispiel: AYpxtcVb.jYmvgB5A5DfQou6kSwS32LvmWUkUclo8):\t")
    wattro_cfg = WattroCfg(domain, api_key)
    minimal_config = {"wattro_cfg": dataclasses.asdict(wattro_cfg)}
    write_path(cfg_file, minimal_config)


def get_or_create() -> SyncCfg:
    """_get or create cfg"""
    cfg_file, created = get_or_create_fp("cfg")
    if created:
        _create_min_cfg(cfg_file)
    logging.info("Lese Konfiguration von %s", cfg_file)
    cfg = read_path(cfg_file)
    wattro_cfg = extract_wattro_cfg(cfg)
    asset_cfg = extract_src_cfg(cfg, "asset")
    project_cfg = extract_src_cfg(cfg, "project")
    mail_cfg = extract_mail_cfg(cfg)
    return SyncCfg(wattro_cfg, asset_cfg, project_cfg, mail_cfg)


def write_mail_cfg(mail_cfg: MailCfg) -> None:
    for key, value in dataclasses.asdict(mail_cfg).items():
        cfg_update("mail", key, value)
