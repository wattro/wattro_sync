from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, Iterator, Iterable


@dataclass
class CollectionInfo:
    collection_name: str
    fields: list[str]
    ident: str

    @classmethod
    def empty(cls) -> CollectionInfo:
        return cls(
            collection_name="empty collection",
            fields=[],
            ident="empty"
        )


@dataclass
class DBRes:
    description: Iterable[str]
    rows: Iterable[tuple]

    def iter_as_dict(self) -> Iterator[dict]:
        for row in self.rows:
            res = {}
            for key, val in zip(self.description, row):
                res[key] = val
            yield res

    def get_dict_list(self) -> list[dict]:
        return list(self.iter_as_dict())


class SrcCli(abc.ABC):
    collection_info: CollectionInfo

    @abc.abstractmethod
    def __init__(self, connection_info: Any):
        ...

    @abc.abstractmethod
    def get_last(
            self,
            order_by_field: str,
            descending: bool = True,
            limit: int = 100,
    ) -> DBRes:
        """
        Get the last `limit` (default:100) entries ordered by `order_by_field`

        Default sorting: Ascending. pass `descending=True` to reverse the sorting.
        """
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
    def get_fields(cls, connection_info: Any, collection: str) -> tuple[list[str], dict[str, list]]:
        """ Get the fields of a collection. And sample values. """
        ...

    @abc.abstractmethod
    def get_new(self, known_idents: tuple) -> DBRes:
        """
        Get all entries on the CollectionInfo collection that are not identified by `known_idents`
        """
        ...

    @classmethod
    @abc.abstractmethod
    def get_healthy_connection(cls, connection_info: Any):
        """Return an instance of this class if `connection_info` can create a healthy connection."""
        ...
