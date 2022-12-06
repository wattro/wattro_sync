#!/bin/env python3
import argparse
import dataclasses
import datetime
import logging
import random
from typing import Iterable, Sequence

import wattro_sync.config_reader.access
import wattro_sync.file_access.read_write
from wattro_sync.api.api_mapping import ApiNameToStructureMapping
from wattro_sync.api.mail import MailApi
from wattro_sync.api.rest_api import WattroNodeApi
from wattro_sync.api.src_cli import SrcCli
from wattro_sync.config_reader.types import (
    SyncCfg,
    ConnectionStructure,
    FieldMapping,
    ConfigDegenerated,
)
from wattro_sync.file_access.logging import get_file_handler, get_stdout_handler
from wattro_sync.hash_history import history
from wattro_sync.helpers import SOURCE_CHOICES, TARGET_NODE_MAPPING


def main() -> int:
    args = parse_args()

    setup_logger(args)
    if not wattro_sync.file_access.read_write.exists("cfg"):
        logging.error(
            "Keine Konfiguration gefunden. Bitte zuerst eine via `setup` erstellen."
        )
        return -1
    cfg: SyncCfg = wattro_sync.config_reader.access.get_or_create()
    mail_api = MailApi(cfg.mail_cfg)

    logging.info("Prüfe Verbindung zu Wattro.")
    try:
        wattro_api = WattroNodeApi.get_healthy_api(**dataclasses.asdict(cfg.wattro_cfg))
    except Exception as err:
        mail_api.send(
            logging.CRITICAL,
            "Verbindung zu Wattro API fehlgeschlagen. Es wurden keine Daten gesendet.",
        )
        logging.critical(err)
        return -1
    logging.info("Verbindung zu Wattro ok.")

    tot_success, tot_fail = 0, 0
    for target in TARGET_NODE_MAPPING:
        if args.limit_target and target not in args.limit_target:
            logging.info(f"Überspringe {target!r}, da nicht in {args.limit_target}.")
            continue
        connection_struct: ConnectionStructure | None = getattr(cfg, target, None)
        if connection_struct is None:
            logging.info(f"Überspringe {target!r}, da keine Konfiguration vorhanden.")
            continue
        con_type = connection_struct.connection_type
        if args.limit_src and con_type not in args.limit_src:
            logging.info(
                f"Überspringe {target}, da {con_type} nicht in {args.limit_src}."
            )
            continue

        success, fail = sync(target, connection_struct, wattro_api, args.dry)
        tot_success += success
        tot_fail += fail

    mail_log_lvl = logging.DEBUG
    tot = tot_fail + tot_success
    msg = "Synchronisation durchgeführt.<br /><br />"
    if tot > 1:
        msg += f"Es wurden {tot} Datensätze bearbeitet.<br />"
    else:
        msg = "Es wurde ein Datensatz bearbeitet.<br />"
    if tot_success > 0:
        mail_log_lvl = logging.INFO
        msg += f"Davon erfolgreich: {tot_success} ({tot_success / tot:.1%}).<br />"
    if tot_fail > 0:
        mail_log_lvl = logging.ERROR
        if tot_fail > 1:
            msg += f"Es traten <strong>{tot_fail} Fehler</strong> auf.<br />"
        else:
            msg += f"Dabei trat <strong>ein Fehler</strong> auf.<br />"

    if args.dry:
        msg += "Da es sich um einen Testaufruf handelt wurden <emph>keine Daten verändert</emph>."

    mail_api.send(mail_log_lvl, msg)

    logging.info("Sync beendet.")
    return 0


def setup_logger(args):
    base_logger = logging.getLogger()
    base_logger.setLevel(logging.INFO)
    file_handler, stdout_handler = get_file_handler(), get_stdout_handler()
    base_logger.addHandler(file_handler)
    base_logger.addHandler(stdout_handler)

    stdout_handler.setLevel(logging.WARNING)
    if args.v or args.dry:
        stdout_handler.setLevel(logging.INFO)
    logging.info(" === Started %s  ===", datetime.datetime.now())
    if args.dry:
        logging.info("Dry Run.")


def sync(
    target: str,
    src_con_struct: ConnectionStructure,
    wattro_api: WattroNodeApi,
    is_dry_run: bool,
) -> tuple[int, int]:
    """returns number of successfull and failed updates"""
    logging.info(
        f"Starte Prozess für {target!r} (Quelle: {src_con_struct.connection_type})"
    )
    source_api_struct = ApiNameToStructureMapping[src_con_struct.connection_type]
    api_class: type[SrcCli] = source_api_struct.api
    try:
        src_api: SrcCli = api_class.get_healthy_connection(src_con_struct.sync_info)
    except ConnectionError:
        logging.error("Prozess für %s abgebrochen.", target)
        return 0, 1
    logging.info("Hole Daten von Wattro...")
    known_idents = wattro_api.get_idents(target)

    logging.info("%s gefunden. Hole neue Daten von Quelle...", len(known_idents))
    hist = history.HistoryHandler()
    ident = src_con_struct.sync_info.collection_info.ident
    src_data_new_idents = src_api.get_new(known_idents)
    logging.info("%s neue gefunden.", len(src_data_new_idents.rows))

    success_updates = 0
    failed_updates = 0
    success = send_to_wattro(
        target, src_con_struct, wattro_api, is_dry_run, src_data_new_idents
    )
    if success and not is_dry_run:
        for val in src_data_new_idents:
            hist.update(target, val, ident)
        hist.save()
    if success:
        success_updates += len(src_data_new_idents)
    else:
        failed_updates += len(src_data_new_idents)

    logging.info("Hole Daten von Quelle...")
    src_data_known_idents = src_api.get_old(known_idents)
    logging.info("%s Datensätze auf Änderung prüfen...", len(src_data_known_idents))

    for changed in hist.iter_changed(target, src_data_known_idents, ident):
        success = send_to_wattro(
            target,
            src_con_struct,
            wattro_api,
            is_dry_run,
            src_data=[changed],
            update=True,
        )
        if success:
            success_updates += 1
            if not is_dry_run:
                hist.update(target, changed, ident)
        else:
            failed_updates += 1
    logging.info(
        f"Sync für %s abgeschlossen. Bearbeitet: %i (erfolgreich: %i | nicht erfolgreich: %i)",
        target,
        success_updates + failed_updates,
        success_updates,
        failed_updates,
    )
    if not is_dry_run and success_updates > 0:
        hist.save()
    return success_updates, failed_updates


def send_to_wattro(
    target: str,
    src_con_struct: ConnectionStructure,
    wattro_api: WattroNodeApi,
    is_dry_run: bool,
    src_data: Sequence[dict],
    update=False,
) -> bool:
    """send to wattro. return Fail if write failed"""
    if len(src_data) == 0:
        return True
    new_target_data = transform(
        src_data, src_con_struct.field_mapping, src_con_struct.encoding
    )
    if is_dry_run:
        count = len(new_target_data)
        logging.info("DRY RUN - Es wurden %i Datensätze erzeugt.", count)
        logging.info("Beispiel Datensätze (quelle --> ziel):")
        k = min(count, 3)
        for i in random.sample(range(count), k=k):
            logging.info("%s --> %s", src_data[i], new_target_data[i])
        return True
    logging.info("Schreibe Daten nach Wattro.")
    success = True
    try:
        if not update:
            wattro_api.bulk_create(target, new_target_data)
        else:
            wattro_api.update_by_ident(target, new_target_data[0])
    except ConnectionError as issue:
        logging.error("Schreiben von %s fehlgeschlagen. %s", new_target_data, issue)
        success = False
    logging.info("abgeschlossen.")
    return success


def transform(
    new_src_data: Iterable[dict], field_mapping: FieldMapping, encoding: str
) -> list[dict]:
    new_data_list = []
    for raw_src in new_src_data:
        if not isinstance(raw_src, dict):
            raise RuntimeError(f"Wrong instance format: {raw_src!r}")
        src = parse_raw_src(raw_src, encoding)
        new_data = {}
        for field_name, field_map in field_mapping.items():
            src_str = field_map["src"]
            if src_str is None:
                continue
            if isinstance(src_str, int):
                raise RuntimeError(
                    "Fehlkonfiguration Feld: {field_name}. Quelle ist fester Wert."
                )
            new_data[field_name] = get_date(field_map, field_name, src, src_str)
        new_data_list.append(new_data)
    return new_data_list


def parse_raw_src(raw_src: dict, encoding: str) -> dict[str, int | str]:
    src: dict[str, int | str] = {}
    for key, val in raw_src.items():
        if val is None:
            src[key] = ""
        elif isinstance(val, bytes):
            try:
                str_val = val.decode(encoding=encoding)
            except UnicodeDecodeError as decode_err:
                logging.warning(decode_err.reason, key, val)
                str_val = val.decode(encoding=encoding, errors="ignore")
            src[key] = str_val
        else:
            src[key] = val
    return src


def get_date(field_map: dict, field_name: str, src: dict, src_str: str) -> int | str:
    try:
        new_date = src_str.format(**src)
    except Exception as eval_fail:
        logging.critical(f"Failed to parse %r on %s for %s", src_str, src, field_name)
        raise eval_fail
    if field_map["type"] in ["field", "int"]:
        return int(new_date)

    max_length = field_map.get("max_length", None)
    if max_length is None:
        return new_date

    if not isinstance(max_length, int):
        raise ConfigDegenerated(f"max_length not a number {max_length=} {field_name=}")

    oneline = new_date.strip().replace("\r", "").replace("\n", " | ")

    if len(oneline) <= max_length:
        return oneline

    shortened = f"{oneline[:max_length - 3]}..."
    logging.info(
        "Eingabe für %r zu groß. Kürze %r ----> %r", field_name, new_date, shortened
    )
    return shortened


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dry",
        action="store_true",
        help="Dry Run. Modifiziert keine Daten. Impliziert -v",
        default=False,
    )
    parser.add_argument(
        "--limit_src",
        help="Schränkt die Quellsysteme ein.",
        choices=SOURCE_CHOICES,
        nargs="*",
    )
    parser.add_argument(
        "--limit_target",
        help="Schränkt die Ziele ein.",
        choices=TARGET_NODE_MAPPING.keys(),
        nargs="*",
    )
    parser.add_argument("-v", help="Setzt das Loglevel auf 'info'", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    exit(main())
