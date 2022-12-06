from __future__ import annotations

import json
import logging
import os
import pathlib
import typing

from wattro_sync.config_reader.types import ConfigDegenerated

BASE_FOLDER = ".wattro_sync"
FILE_NAMES = ["cfg.json", "history.json", "mail.json"]
CON_TYPE_KEY = "connection_type"
CON_INFO_KEY = "connection_info"
FIELD_MAP_KEY = "field_mapping"

ShortType = typing.Literal["cfg", "history", "mail"]


def exists(file_type: ShortType) -> bool:
    fp = _get_file_path(file_type)
    return fp.exists()


def get_or_create(file_type: ShortType) -> tuple[pathlib.Path, bool]:
    """
    file_path, created = get_or_create('cfg')
    """
    created = False
    file_path = _get_file_path(file_type)
    if not file_path.is_file():
        created = True
        write_path(file_path, {})
    return file_path, created


def write_path(file_path: pathlib.Path, val: typing.Any, pretty: bool = False) -> None:
    if file_path.exists():
        logging.info("Overwriting exsiting file %s", file_path)
    txt = ""
    if pretty:
        txt = json.dumps(val, indent=4, sort_keys=True)
    else:
        txt = json.dumps(val)
    file_path.write_text(txt)


def write(file_type: ShortType, val: typing.Any) -> None:
    file_p, _ = get_or_create(file_type)
    return write_path(file_p, val)


def read_path(file_path: pathlib.Path) -> dict:
    try:
        raw_read = json.loads(file_path.read_text())
    except (json.decoder.JSONDecodeError, AssertionError) as mal_cfg:
        raise ConfigDegenerated(f"{file_path} could not be parsed.") from mal_cfg
    if not isinstance(raw_read, dict):
        raise ConfigDegenerated(f"{file_path} not a dict.")
    return raw_read


def read(file_type: ShortType) -> dict:
    file_p, _ = get_or_create(file_type)
    return read_path(file_p)


def update(file_type: ShortType, target: str, key: str, val: typing.Any) -> None:
    file_p, _ = get_or_create(file_type)
    file_dict = read_path(file_p)
    if target in file_dict:
        if key in file_dict[target]:
            logging.warning(
                "Overwriting existing value for '%s' in '%s'. Old value: '%s'. New value: %s",
                key,
                target,
                file_dict[target][key],
                val,
            )
    else:
        file_dict[target] = {}
    file_dict[target].update({key: val})
    write_path(file_p, file_dict, pretty=(file_type == "cfg"))


def hist_update(target: str, key: str, val: typing.Any) -> None:
    return update("history", target, key, val)


def cfg_update(target: str, key: str, val: typing.Any) -> None:
    return update("cfg", target, key, val)


def cfg_rm() -> None:
    """removes the config file"""
    file_path = _get_file_path("cfg")
    if not file_path.is_file():
        logging.info("Nothing to do.")
        return
    os.unlink(file_path)


def get_base_folder_path() -> pathlib.Path:
    """Path where all configs and logs are stored"""
    return pathlib.Path.home() / BASE_FOLDER


def _get_or_create_base_folder() -> pathlib.Path:
    """gets or creates wattro config folder"""
    wattro_folder = get_base_folder_path()
    if not wattro_folder.is_dir():
        logging.info("Erzeuge Wattro Konfig Ordner: %s", wattro_folder)
        os.mkdir(wattro_folder)
    return wattro_folder


def _get_file_path(file_type: ShortType) -> pathlib.Path:
    folder = _get_or_create_base_folder()
    file_name = [x for x in FILE_NAMES if x.startswith(file_type)]
    if not len(file_name) == 1:
        raise FileNotFoundError(f"{file_type!r} is no valid selection.")
    return folder / file_name.pop()
