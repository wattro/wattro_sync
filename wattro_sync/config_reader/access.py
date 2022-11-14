from __future__ import annotations

import dataclasses
import json
import logging
import os
import pathlib
import typing

from .types import SyncCfg, WattroCfg, ConnectionStructure
from ..api.api_mapping import ApiNameToStructureMapping, ApiStructure

CFG_FOLDER = ".wattro_sync"
CFG_FILE_NAME = "cfg.json"

CON_TYPE_KEY = "connection_type"
CON_INFO_KEY = "connection_info"
FIELD_MAP_KEY = "field_mapping"


def extract_wattro_cfg(cfg: dict) -> WattroCfg:
    """read wattro cfg form file"""
    assert "wattro_cfg" in cfg, f"'wattro_cfg' fehlt in {cfg}."
    return WattroCfg(**cfg["wattro_cfg"])


def extract_src_cfg(cfg: dict, target: str) -> ConnectionStructure | None:
    """read asset cfg form file"""
    if target not in cfg:
        logging.info("Keine Konfiguration für %s. (Verfügbar: %s)", target, cfg.keys())
        return None
    asset_cfg = cfg[target]
    con_type = asset_cfg["connection_type"]
    api_structure: ApiStructure = ApiNameToStructureMapping[con_type]

    con_info_data = asset_cfg['connection_info']
    con_info = api_structure.connection_info(**con_info_data)

    return ConnectionStructure(connection_type=con_type, connection_info=con_info)


def write_connection_structure(target: str, connection_structure: ConnectionStructure) -> None:
    _write(target, CON_TYPE_KEY, connection_structure.connection_type)
    _write(target, CON_INFO_KEY, dataclasses.asdict(connection_structure.connection_info))


def write_field_mapping(target: str, field_mapping: dict) -> None:
    _write(target, FIELD_MAP_KEY, field_mapping)


def _write(target: str, key: str, val: typing.Any) -> None:
    cfg_file = get_or_create_cfg_file_path()
    cfg_raw = _read_from_file(cfg_file)
    if target in cfg_raw:
        if key in cfg_raw[target]:
            logging.warning(
                "Overwriting existing value for '%s' in '%s'. Old value: '%s'. New value: %s",
                key,
                target,
                cfg_raw[target][key],
                val,
            )
    else:
        cfg_raw[target] = {}
    cfg_raw[target].update({key: val})
    _write_to_file(cfg_file, cfg_raw)


def rm() -> None:
    """removes the config file"""
    file_path = pathlib.Path.home() / CFG_FOLDER / CFG_FILE_NAME
    if not file_path.is_file():
        logging.info("Nothing to do.")
        return
    os.unlink(file_path)


def exists() -> bool:
    """CFG_FILE_NAME exsits in CFG_FOLDER in home"""
    cfg_folder_path = pathlib.Path.home() / CFG_FOLDER
    return cfg_folder_path.is_dir() and (cfg_folder_path / CFG_FILE_NAME).is_file()


def get_or_create() -> SyncCfg:
    """get or create cfg"""
    cfg_file = get_or_create_cfg_file_path()
    logging.info("Lese Konfiguration von %s", cfg_file)
    cfg = _read_from_file(cfg_file)
    wattro_cfg = extract_wattro_cfg(cfg)
    asset_cfg = extract_src_cfg(cfg, "asset")
    return SyncCfg(wattro_cfg, asset_cfg)


def get_or_create_cfg_file_path() -> pathlib.Path:
    """Get or create config file path."""
    cfg_folder = _get_or_create_cfg_folder()
    cfg_file = cfg_folder / CFG_FILE_NAME
    if not cfg_file.is_file():
        _create_min_cfg(cfg_file)
    return cfg_file


def _get_or_create_cfg_folder() -> pathlib.Path:
    """gets or creates wattro config folder"""
    wattro_folder = pathlib.Path.home() / CFG_FOLDER
    if not wattro_folder.is_dir():
        logging.info("Erzeuge Wattro Konfig Ordner: %s", wattro_folder)
        os.mkdir(wattro_folder)
    return wattro_folder


def _create_min_cfg(cfg_file: pathlib.Path) -> None:
    """Create Minimal Config."""
    print(f"Erzeuge Konfiguration in {cfg_file}. Bitte Informationen eingeben:")
    domain = input("Kunden Domain (Beispiel: `wattro`):\t")
    api_key = input("Api Key (Beispiel: AYpxtcVb.jYmvgB5A5DfQou6kSwS32LvmWUkUclo8):\t")
    wattro_cfg = WattroCfg(domain, api_key)
    minimal_config = {"wattro_cfg": dataclasses.asdict(wattro_cfg)}
    _write_to_file(cfg_file, minimal_config)


def _write_to_file(file_path: pathlib.Path, val: typing.Any) -> None:
    txt = json.dumps(val, indent=4, sort_keys=True)
    file_path.write_text(txt)


def _read_from_file(file_path: pathlib.Path) -> typing.Any:
    return json.loads(file_path.read_text())
