import logging
from typing import overload, Literal


class StupidTerminalChoice:
    def __init__(self, menu_entries: list, **kwargs):
        self.menu_entries = menu_entries
        self.kwargs = kwargs

    def _is_multi(self) -> bool:
        key = "multi_select"
        return self.kwargs.get(key, False)

    def show(self) -> int | tuple[int, ...] | None:
        print(f"\n\n##\n {self.kwargs.get('title', 'Auswahl:')}")
        print("[q]\t keins davon")
        for i, entry in enumerate(self.menu_entries):
            print(f"[{i}]\t {entry}")
        if self._is_multi():
            choices = input("Auswahl (etwa 0 2 3):\n").split(" ")
            if len(choices) == 1 and choices[0] == "q":
                return None
            return tuple(int(x) for x in choices if x != "")
        # else
        choice = input("Auswahl (etwa 0)\n").strip()
        if choice == "q":
            return None
        return int(choice)


try:
    from simple_term_menu import TerminalMenu
except NotImplementedError as platform_err:
    TerminalMenu = StupidTerminalChoice
    logging.warning(f"{platform_err} - falling back to {TerminalMenu!r}")

from wattro_sync.api.api_mapping import ApiNameToStructureMapping

SOURCE_CHOICES = ApiNameToStructureMapping.keys()
TARGET_NODE_MAPPING = {"project": "/project/project/", "asset": "/node/asset/"}


# TerminalMenu Helpers
@overload
def multi_select(
    menu_entries: list[str], required: Literal[True], **kwargs
) -> tuple[int]:
    ...


@overload
def multi_select(
    menu_entries: list[str], required: Literal[False], **kwargs
) -> None | tuple[int]:
    ...


def multi_select(
    menu_entries: list[str], required: bool = False, **kwargs
) -> None | tuple[int]:
    is_multi = kwargs.pop("multi_select", True)
    res = _select(menu_entries, is_multi, required, **kwargs)
    if isinstance(res, int):
        raise RuntimeError("Failed to parse mutli select", res)
    return res


@overload
def select(menu_entries: list[str], required: Literal[True], **kwargs) -> int:
    ...


@overload
def select(menu_entries: list[str], required: Literal[False], **kwargs) -> None | int:
    ...


def select(menu_entries: list[str], required: bool = False, **kwargs) -> None | int:
    is_multi = kwargs.pop("multi_select", False)
    res = _select(menu_entries, is_multi, required, **kwargs)
    if isinstance(res, tuple):
        raise RuntimeError("Failed to parse single value", res)
    return res


def _select(
    menu_entries: list[str], is_multi: bool, required: bool, **kwargs
) -> None | int | tuple[int]:
    is_many = len(menu_entries) > 7
    res = TerminalMenu(
        menu_entries,
        **kwargs,
        multi_select=is_multi,
        show_multi_select_hint=is_multi,
        show_multi_select_hint_text="<Leertaste> um an/abzuwählen, <Enter> um anzuwählen und abzuschließen.",
        show_search_hint=is_many and not is_multi,
        show_search_hint_text="'/' Eingeben um Filter zu starten",
    ).show()
    if required and (res is None or res == []):
        input("Pflichtfeld. (Enter drücken um erneut zu wählen).")
        return _select(menu_entries, is_multi, required, **kwargs)
    return res
