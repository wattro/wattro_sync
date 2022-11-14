#!/bin/env python3
import argparse
import logging
import pathlib

from wattro_sync.config_reader.types import ConnectionStructure
from wattro_sync.helpers import (
    SOURCE_CHOICES,
    TARGET_NODE_MAPPING,
    multi_select,
    select,
)
from .api.api_mapping import ApiNameToStructureMapping, ApiStructure
from .api.rest_api import WattroNodeApi
from .api.sqlite_api import SQLiteSyncInfo, SQLiteApi
from .api.src_cli import CollectionInfo
from .config_reader import access as cfg_access


def main() -> int:
    args = parse_args()
    if args.v:
        logging.basicConfig(level=logging.INFO)
    cfg_existed = cfg_access.exists()
    cfg = cfg_access.get_or_create()
    wattro_api = None
    if not cfg_existed:
        wattro_api = get_wattro_api_or_none(cfg)
        if wattro_api is None:
            logging.info("Lösche potentiell fehlerhafte Konfiguration")
            cfg_access.rm()
            return -1

    logging.info("Erzeuge Konfiguration für %s -> %s", args.source, args.target)
    api_struct: ApiStructure = ApiNameToStructureMapping[args.source]
    if api_struct.connection_info == SQLiteSyncInfo:
        connection_info_class = setup_sqlite()
    else:
        raise NotImplementedError(f"TODO {api_struct}")

    logging.info("Prüfe '%s' Verfügbarkeit.", args.source)
    try:
        _api = api_struct.api.get_healthy_connection(connection_info_class)
    except Exception as err:
        logging.critical(
            "Verbindung zu %s fehlgeschlagen: %s. Konfiguration wurde nicht gespeichert",
            args.source,
            err,
        )
        return -1

    con_struct = ConnectionStructure(
        connection_type=args.source,
        connection_info=connection_info_class,
    )
    cfg_access.write_connection_structure(args.target, con_struct)
    logging.info("Verbindungsdaten wurden gespeichert.")

    if wattro_api is None:
        wattro_api = get_wattro_api_or_none(cfg)
        if wattro_api is None:
            return -1

    raw_fields = wattro_api.get_fields(TARGET_NODE_MAPPING[args.target])

    field_mapping = {}

    src_fields = connection_info_class.table_info.fields
    for key, value in raw_fields.items():
        if value.get("read_only", True):
            logging.info("Überspringe 'read only' Feld %s; %s", key, value)
            continue
        field_mapping[key] = {**value, "src": select_src(key, src_fields, value)}

    cfg_access.write_field_mapping(args.target, field_mapping)
    print(
        f"Synchronisations Konfiguration für {args.target!r} mit Quelle {args.source!r} gespeichert."
    )

    return 0


def select_src(key: str, src_fields: list[str], value: dict) -> str | None:
    can_multi_select = value["type"] == "string"
    src = (
        _select_one(key, src_fields, value)
        if not can_multi_select
        else _select_for_string(key, src_fields, value)
    )
    logging.info("%s <-- %s", key, src)
    return src


def _select_for_string(key: str, src_fields: list[str], value: dict) -> str | None:
    required = value["required"]
    choices = multi_select(
        src_fields,
        required=required,
        title=f"Felder für {key} [Typ: string]{_skip_text(required)}",
    )
    if not choices:
        return None
    cfg_fields = [_make_cfg_field(src_fields[i]) for i in choices]
    return ", ".join(cfg_fields)


def _select_one(key: str, src_fields: list[str], value: dict) -> str | None:
    required = value["required"]
    choice = select(
        src_fields,
        required=required,
        title=f"Feld für {key} [Typ: {value['type']}]{_skip_text(required)}",
    )
    if choice is None:
        return None
    return _make_cfg_field(src_fields[choice])


def _skip_text(required: bool) -> str:
    if required:
        return "\t(Überspringen: q)"
    return ""


def _make_cfg_field(field_name: str) -> str:
    return "{src['" + field_name + "']}"


def get_wattro_api_or_none(cfg) -> WattroNodeApi | None:
    logging.info("Prüfe Wattro API Verfügbarkeit.")
    try:
        wattro_api = WattroNodeApi.get_healthy_api(
            domain=cfg.wattro_cfg.domain, api_key=cfg.wattro_cfg.api_key
        )
    except ConnectionError as err:
        logging.critical(
            "Verbindung zu Wattro API fehlgeschlagen: %s",
            err,
        )
        return None
    logging.info("Wattro API erreichbar unter %s", wattro_api.hostname)
    return wattro_api


def setup_sqlite() -> SQLiteSyncInfo:
    while True:
        db_path_str = input("Pfad zur Datenbank Datei (z.B. 'db.sqlite3'):\t")
        db_path = pathlib.Path(db_path_str).resolve()
        if db_path.is_file():
            break
        logging.error(" '%s' muss ein Pfad zu einer gültigen Datei sein.", db_path)
    table_options = sorted(SQLiteApi.get_collections(db_path))
    table_id = select(
        table_options, required=True, title="Quelltabelle (Enter zum Auswählen)"
    )
    table_name = table_options[table_id]

    field_options, field_samples = SQLiteApi.get_fields(db_path, table_name)
    field_ids = multi_select(
        field_options,
        required=True,
        title="Felder, die verwendet werden sollen",
        preview_title="Beispiel Werte",
        preview_command=lambda field_name: ", ".join(
            [str(x) for x in field_samples[field_name]]
        ),
    )

    field_choices = [
        field for idx, field in enumerate(field_options) if idx in field_ids
    ]
    identifier = field_choices[
        select(
            field_choices,
            required=True,
            title="Primärschlüssel (Feld, welches den Datensatz eindeutig identifiziert)",
        )
    ]
    return SQLiteSyncInfo(
        db_path, CollectionInfo(table_name, field_choices, identifier)
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("target", help="Daten Ziel", choices=TARGET_NODE_MAPPING.keys())
    parser.add_argument("source", help="Quellsystem", choices=SOURCE_CHOICES)

    parser.add_argument("-v", help="Setzt das Loglevel auf 'info'", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    exit(main())
