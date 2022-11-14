#!/bin/env python3
import argparse
import logging

from wattro_sync.config_reader import access as cfg_access
from wattro_sync.config_reader.types import SyncCfg, ConnectionStructure
from wattro_sync.helpers import SOURCE_CHOICES, TARGET_NODE_MAPPING


def main() -> int:
    args = parse_args()
    if args.v or args.dry:
        logging.basicConfig(level=logging.INFO)
        if args.dry:
            logging.info("Dry Run.")
    if not cfg_access.exists():
        logging.error("Keine Konfiguration gefunden. Bitte zuerst eine via `setup` erstellen.")
        return -1
    cfg: SyncCfg = cfg_access.get_or_create()

    for target in TARGET_NODE_MAPPING:
        if args.limit_target and target not in args.limit_target:
            logging.info(f"Überspringe {target}, da nicht in {args.limit_target}.")
            continue
        connection_struct_data: ConnectionStructure | None = getattr(cfg, target, None)
        if connection_struct_data is None:
            logging.info(f"Überspringe {target}, da keine Konfiguration vorhanden.")
            continue
        con_type = connection_struct_data.connection_type
        if args.limit_src and con_type not in args.limit_src:
            logging.info(f"Überspringe {target}, da {con_type} nicht in {args.limit_src}.")
            continue

        logging.info(f"Start sync: {target} (Quelle: {con_type})")

    logging.info("Sync beendet.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("--dry", action="store_true", help="Dry Run. Modifiziert keine Daten. Impliziert -v",
                        default=False)
    parser.add_argument("--limit_src", help="Schränkt die Quellsysteme ein.", choices=SOURCE_CHOICES, nargs='*')
    parser.add_argument("--limit_target", help="Schränkt die Ziele ein.", choices=TARGET_NODE_MAPPING.keys(),
                        nargs='*')
    parser.add_argument("-v", help="Setzt das Loglevel auf 'info'", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    exit(main())
