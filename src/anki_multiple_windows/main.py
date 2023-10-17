from __future__ import annotations

from collections.abc import Callable
from inspect import stack
from typing import Any

from aqt import DialogManager
from aqt import gui_hooks
from aqt import Qt
from aqt.utils import KeyboardModifiersPressed


def open(self: DialogManager, name: str, *args: Any, **kwargs: Any) -> Any:
    creator, instances = self._dialogs[name]

    if KeyboardModifiersPressed().shift or not instances:
        instance = creator(*args, **kwargs)

        self._dialogs[name][1].append(instance)
    else:
        instance = instances[0]

        if instance.windowState() & Qt.WindowState.WindowMinimized:
            instance.setWindowState(instance.windowState() & ~Qt.WindowState.WindowMinimized)
        instance.activateWindow()
        instance.raise_()
        if hasattr(instance, "reopen"):
            instance.reopen(*args, **kwargs)

    gui_hooks.dialog_manager_did_open_dialog(self, name, instance)
    return instance


def markClosed(self: DialogManager, name: str) -> None:
    if len(self._dialogs[name][1]) > 1:
        caller = stack()[1].frame.f_locals["self"]
        self._dialogs[name][1].remove(caller)
    else:
        self._dialogs[name][1] = []


def closeAll(self: DialogManager, onsuccess: Callable[[], None]) -> bool | None:
    if self.allClosed():
        onsuccess()
        return None

    def callback() -> None:
        if self.allClosed():
            onsuccess()
        else:
            pass

    for _, (_, instances) in self._dialogs.items():
        for instance in instances:
            if getattr(instance, "silentlyClose", False):
                instance.close()
                callback()
            else:
                instance.closeWithCallback(callback)

    return True


def main() -> None:
    for name in DialogManager._dialogs:
        DialogManager._dialogs[name][1] = []

    DialogManager.open = open
    DialogManager.markClosed = markClosed
    DialogManager.closeAll = closeAll
