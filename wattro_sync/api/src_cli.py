from __future__ import annotations

import abc
import logging
from dataclasses import dataclass
from typing import Any, Iterator, Sequence, overload


class SyncInfo(abc.ABC):
    collection_info: CollectionInfo

    @abc.abstractmethod
    def asdict(self) -> dict:
        ...

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, info: dict):
        ...


@dataclass
class CollectionInfo:
    collection_name: str
    fields: list[str]
    ident: str
    hardcoded_select: None | str = None

    @classmethod
    def empty(cls) -> CollectionInfo:
        return cls(collection_name="empty collection", fields=[], ident="empty")


@dataclass
class DBRes(Sequence):
    description: Sequence[str]
    rows: Sequence[tuple]

    def _dictify_row(self, row: tuple) -> dict:
        return {key: val for key, val in zip(self.description, row)}

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self) -> Iterator[dict]:
        return (self._dictify_row(row) for row in self.rows)

    @overload
    def __getitem__(self, index: int) -> dict:
        ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[dict]:
        ...

    def __getitem__(self, index: int | slice) -> dict | Sequence[dict]:
        if isinstance(index, int):
            return self._dictify_row(self.rows[index])
        return [self._dictify_row(row) for row in self.rows[index]]


class SrcCli(abc.ABC):
    collection_info: CollectionInfo

    def _qry(self, restrict: str) -> str:
        select = (
            self.collection_info.hardcoded_select
            or f"SELECT {','.join(self.collection_info.fields)} FROM {self.collection_info.collection_name}"
        )
        return f"{select} {restrict.strip(';')};"

    @classmethod
    def get_healthy_connection(cls, sync_info: SyncInfo):
        inst = cls(sync_info)
        try:
            sample = inst.get_sample()
        except Exception as exc_info:
            logging.error(f"Failed to get API: {exc_info}")
            raise ConnectionError("Failed to get API") from exc_info
        logging.debug(
            "Successfully sampled %s: %s",
            sync_info.collection_info.collection_name,
            sample,
        )
        return inst

    def get_sample(self) -> DBRes:
        """
        Get Sample entry
        """
        return self._exec(self._qry("LIMIT 1"))

    def get_new(self, known_idents: Sequence[str]) -> DBRes:
        """
        Get all entries on the CollectionInfo collection that are not identified by `known_idents`
        """
        restrict = ""
        if len(known_idents) > 0:
            restrict = f"WHERE {self.collection_info.ident} NOT IN ({','.join(['?' for _ in known_idents])})"
        qry = self._qry(restrict)
        return self._exec(qry, known_idents)

    def get_old(self, known_idents: Sequence[str]) -> DBRes:
        if len(known_idents) == 0:
            return DBRes([], [])
        restrict = f"WHERE {self.collection_info.ident} IN ({','.join(['?' for _ in known_idents])})"
        qry = self._qry(restrict)
        return self._exec(qry, known_idents)

    @abc.abstractmethod
    def __init__(self, sync_info: SyncInfo):
        ...

    @abc.abstractmethod
    def _exec(self, qry: str, params=None) -> DBRes:
        ...

    @classmethod
    @abc.abstractmethod
    def get_collections(cls, connection_info: Any) -> list[str]:
        """
        Get a list of collections in the src
        """
        ...

    @classmethod
    @abc.abstractmethod
    def get_fields(
        cls, connection_info: Any, collection: str
    ) -> tuple[list[str], dict[str, list]]:
        """
        get_fields(%connection_info%, 'CollectionToScan')
        returns a tuple of
        - list of field names (str)
        - list of a list of up to 10 sample values
        """
        ...
