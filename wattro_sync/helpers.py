from typing import overload, Literal

from simple_term_menu import TerminalMenu

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
    assert is_multi, "Deprecated. Use select instead."
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
    assert not is_multi, "Deprecated. Use multi_select instead."
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
