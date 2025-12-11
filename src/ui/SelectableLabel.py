from PySide6.QtCore import Qt, QPoint, Signal, QSettings
from PySide6.QtWidgets import QApplication, QLabel, QMenu
import webbrowser

class SelectableLabel(QLabel):
    lookup_word = Signal(str)
    settings = QSettings("KrossWordz", "KrossWordz")

    def __init__(self, parent=None, text=None):
        super().__init__(parent=parent, text=text)

        self.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        #self.setFocusPolicy(Qt.ClickFocus)  # needed for keyboard selection

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

    def _show_menu(self, pos: QPoint):
        menu = QMenu(self)
        copy_action = menu.addAction("Copy")
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(self.selectedText()) if self.hasSelectedText() else None)

        select_all_action = menu.addAction("Select All")
        select_all_action.triggered.connect(lambda: self.setSelection(0, len(self.text())))

        for linkName, link in self.settings.value("custom_lookup") or []:
            action = menu.addAction(f"Lookup in {linkName}")
            action.triggered.connect(lambda _, link=link: webbrowser.open(link.format(word = self.selectedText()), new=2))

        menu.exec(self.mapToGlobal(pos))

