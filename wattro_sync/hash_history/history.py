import hashlib
import json
from typing import Literal, NewType, Iterable, Iterator

from ..file_access import read_write

Target = Literal["asset", "project"]

HashHistory = NewType("HashHistory", dict[str, str])


class HistoryHandler:
    def __init__(self):
        self.full_hist = read_write.read("history")

    def iter_changed(
        self, target: str, to_check: Iterable[dict], ident: str
    ) -> Iterator[dict]:
        ident = ident
        hist = self.full_hist.get(target, {})
        for val in to_check:
            key = str(val[ident])
            if hist.get(key, None) != _hashed(val):
                yield val

    def update(self, target: str, val: dict, ident: str) -> None:
        ident = ident
        key = str(val[ident])
        if target not in self.full_hist:
            self.full_hist[target] = {}
        self.full_hist[target][key] = _hashed(val)

    def save(self) -> None:
        read_write.write("history", self.full_hist)


def _generate_from_values(new_values: Iterable[dict], ident: str) -> HashHistory:
    """_generate_from_values a hash history from new values, using ident as the key"""
    return HashHistory({str(val[ident]): _hashed(val) for val in new_values})


def _hashed(raw_dict: dict) -> str:
    """generate hash value from a dict that can be json serialized."""
    # sort_keys: make stable under dict shuffle
    seed = json.dumps(
        {key: f"{val}" for key, val in raw_dict.items()}, sort_keys=True
    ).encode()
    hashed = hashlib.md5(seed, usedforsecurity=False)
    return hashed.hexdigest()
