from PySide6.QtWidgets import QWidget, QVBoxLayout,QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QToolButton, QToolTip, QStyle 
from PySide6.QtCore import Qt, QSettings, QDir

class preferences(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.gemini_api_key = None 
        self.settings= QSettings("KrossWordz", "KrossWordz")
        self.gemini_key_input = QVBoxLayout()
        self.gemini_api_key_label = QLabel("Gemini API Key")
        self.gemini_api_key_input = QLineEdit()
        if self.settings.value("gemini_api_key"):
            self.gemini_api_key_input.setText(self.settings.value("gemini_api_key"))

        self.gemini_key_input.addWidget(self.gemini_api_key_label)
        self.gemini_key_input.addWidget(self.gemini_api_key_input)
        self.layout.addLayout(self.gemini_key_input)

        self.directory_input = QVBoxLayout()
        self.puzzles_dir_label = QLabel("Puzzles Directory")

        row = QHBoxLayout()
        browse_btn = QPushButton("Browse... ")
        browse_btn.clicked.connect(self.pick_puzzles_dir)

        self.puzzles_dir_input = QLineEdit()
        row.addWidget(self.puzzles_dir_input)
        row.addWidget(browse_btn)

        if self.settings.value("puzzles_dir"):
            self.puzzles_dir_input.setText(self.settings.value("puzzles_dir"))

        self.directory_input.addWidget(self.puzzles_dir_label)
        self.directory_input.addLayout(row)

        self.layout.addLayout(self.directory_input)

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self._save_settings)

        self.customLookupLabel()

        self.layout.addWidget(self.apply_button)

    def customLookupLabel(self):
        title_row = QHBoxLayout()
        self.customLookupLabel = QLabel("Custom Lookup")

        self.help = HelpTooltipButton("Enter custom links to lookup words. The link must include {word} to represent the word. Here is an example for onelook https://www.onelook.com/?w={word}")

        title_row.addWidget(self.customLookupLabel)
        title_row.addWidget(self.help)
        title_row.addStretch()

        self.layout.addLayout(title_row)

        self.existingLinks = self.settings.value("custom_lookup").copy() if self.settings.value("custom_lookup") else []

        for linkName, link in self.existingLinks:
            row = QHBoxLayout()
            linkNameLabel = QLabel(linkName)
            linkLabel = QLabel(link)
            row.addWidget(linkNameLabel)
            row.addWidget(linkLabel)
            deleteLink = QPushButton("Remove")

            def delete(_=None, link=link, row=row, editableLink=linkLabel, linkName=linkName, deleteLink=deleteLink):
                linkNameLabel.deleteLater()
                editableLink.deleteLater()
                deleteLink.deleteLater()
                row.deleteLater()
                self.existingLinks.remove((linkName, link))

            deleteLink.clicked.connect(delete)
            row.addWidget(deleteLink)
            self.layout.addLayout(row)

        addButton = QPushButton("Add")
        addButton.setDisabled(True)
        addButton.clicked.connect(self.addCustomLookup)

        self.newEditableLinkRow = QHBoxLayout()
        self.newLinkName = QLineEdit("")
        self.newEditableLink = QLineEdit("")

        self.newEditableLink.textChanged.connect(lambda text: addButton.setDisabled(True) if text == "" or (text in map(lambda x: x[1], self.existingLinks) ) else (addButton.setDisabled(False) if self.newLinkName.text() != "" and self.newLinkName.text() not in map(lambda x: x[0], self.existingLinks) else addButton.setDisabled(True)))
        self.newLinkName.textChanged.connect(lambda text: addButton.setDisabled(True) if text == "" or (text in map(lambda x: x[0], self.existingLinks) )  else (addButton.setDisabled(False) if self.newEditableLink.text() != "" and self.newEditableLink.text() not in map(lambda x: x[1], self.existingLinks) else addButton.setDisabled(True)))
        self.newEditableLinkRow.addWidget(self.newLinkName)
        self.newEditableLinkRow.addWidget(self.newEditableLink)

        self.newEditableLinkRow.addWidget(addButton)

        self.layout.addLayout(self.newEditableLinkRow)

    def addCustomLookup(self):
       text = self.newEditableLink.text()
       linkName = self.newLinkName.text()
       self.existingLinks.append((linkName, text))
       i = self.index_of_layout(self.layout, self.newEditableLinkRow)

       if i == -1:
           return

       row = QHBoxLayout()
       linkNameLabel = QLabel(linkName)
       editableLink = QLabel(text)
       row.addWidget(linkNameLabel)
       row.addWidget(editableLink)
       deleteLink = QPushButton("Remove")

       # could just refactor this...
       def delete():
           linkNameLabel.deleteLater()
           editableLink.deleteLater()
           deleteLink.deleteLater()
           row.deleteLater()
           self.existingLinks.remove((linkName,text))

       deleteLink.clicked.connect(delete)
       row.addWidget(deleteLink)

       self.newEditableLink.setText("")
       self.newLinkName.setText("")

       self.layout.insertLayout(i, row)

    def index_of_layout(self, parent_layout, target_layout):
        for i in range(parent_layout.count()):
            item = parent_layout.itemAt(i)
            if item.layout() is target_layout:
                return i
        return -1

    def pick_puzzles_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select Directory", self.settings.value("puzzles_dir") or QDir.homePath())
        if path:
            self.puzzles_dir_input.setText(path)

    def _save_settings(self): 
        self.settings.setValue("gemini_api_key", self.gemini_api_key_input.text())
        self.settings.setValue("puzzles_dir", self.puzzles_dir_input.text())
        self.settings.setValue("custom_lookup", self.existingLinks)



class HelpTooltipButton(QToolButton):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setToolTip(text)
        #self.setAutoRaise(True)  # flat look
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxQuestion))

    def enterEvent(self, event):
        # Show immediately on hover, anchored to bottom-left of the button
        pos = self.mapToGlobal(self.rect().bottomLeft())
        QToolTip.showText(pos, self.toolTip(), self)
        super().enterEvent(event)
