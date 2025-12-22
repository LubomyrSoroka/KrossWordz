import math
from ui.SelectableLabel import SelectableLabel
from PySide6.QtCore import Qt, QPoint, QTimer, QEasingCurve, Signal
from PySide6.QtGui import QFont, QTextCursor, QTextDocument, QMouseEvent
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
    QScrollArea,
    QFrame,
)


class CluesTextEdit(SelectableLabel):
    """Text edit styled for clues that forwards navigation keys to the parent."""


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setWordWrap(True)
        self.setTextFormat(Qt.RichText)
        self.pos = None
  
    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            if ev.modifiers() & Qt.ShiftModifier:
                # Create a new event with Shift removed
                new_ev = QMouseEvent(
                    ev.type(),
                    ev.position(),      # or ev.pos() in PyQt5
                    ev.globalPosition(),# or ev.globalPos() in PyQt5
                    ev.button(),
                    ev.buttons(),
                    ev.modifiers() & ~Qt.ShiftModifier
                )
                super().mousePressEvent(new_ev)
            else:
                parent = self.parentWidget()
                if parent is not None: 
                    parent.mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if ev.buttons() & Qt.LeftButton and ev.modifiers() & Qt.ShiftModifier:
            # remove Shift for drag
            new_ev = QMouseEvent(
                ev.type(),
                ev.position(),
                ev.globalPosition(),
                ev.button(),
                ev.buttons(),
                ev.modifiers() & ~Qt.ShiftModifier
            )
            super().mouseMoveEvent(new_ev)
            return
        super().mouseMoveEvent(ev) 


    def setText(self, text):
        """Set clue text and resize the label to tightly wrap the content."""
        super().setText(text)
        self._shrink_to_fit()

    def keyPressEvent(self, event):  # noqa: N802 (Qt interface)
        if event.key() in (
            Qt.Key_Left,
            Qt.Key_Right,
            Qt.Key_Up,
            Qt.Key_Down,
            Qt.Key_Space,
            Qt.Key_Tab,
        ):
            event.ignore()
        else:
            super().keyPressEvent(event)



    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._shrink_to_fit()


    def _shrink_to_fit(self) -> None:
        """Match label height to wrapped text height."""
        available_width = self.width()
        if available_width <= 0:
             return

        margins = self.contentsMargins()
        text_width = max(1, available_width - (margins.left() + margins.right()))

        doc = QTextDocument()
        doc.setDefaultFont(self.font())
        doc.setHtml(self.text())
        doc.setDocumentMargin(0)
        doc.setTextWidth(text_width)

        height = math.ceil(max(doc.size().height(), self.fontMetrics().height()))
        height += margins.top() + margins.bottom()

        self.setMinimumHeight(height)
        self.setMaximumHeight(height)


class CluesPanel(QWidget):
    clue_selected = Signal(int, str)

    """Container showing across and down clues side by side."""

    def __init__(self, across_clues: list[str], down_clues: list[str], parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(10)
        self.setLayout(self.layout)
        self.clues = dict()
        self.clue_texts = dict()

        self._scroll_areas = dict()
        self._highlighted_key = None
        self._side_highlighted_key = None
        self.highlight_color = "#47c8ff"
        self.default_color = self.palette().color(parent.backgroundRole()).name()
        self.scroll_layout = None
        self.across_text_edit = self._create_section(self.layout, "ACROSS", across_clues)
        self.down_text_edit = self._create_section(self.layout, "DOWN", down_clues)
        self.referenced_clues = []
        self.styleSheets = dict()
    

    def _create_section(self, parent_layout: QHBoxLayout, title: str, clues: list[str] ) -> CluesTextEdit:
        container = QWidget(self)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        section_layout = QVBoxLayout()
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(4)
        container.setLayout(section_layout)

        label = QLabel(title)
        label.setFont(QFont("Arial", 11, QFont.Bold))
        section_layout.addWidget(label)

        scroll_area = QScrollArea(container)
        # Remove the default frame; styling the viewport alone won't hide it.
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        scroll_area.viewport().setStyleSheet("background-color: transparent;")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        section_layout.addWidget(scroll_area)
        self._scroll_areas[title.lower()] = scroll_area

        scroll_content = QWidget(scroll_area)
        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(8)
        scroll_content.setLayout(self.scroll_layout)
        scroll_area.setWidget(scroll_content)

        last_text_edit = None

        for clue in clues:
            clue_widget = ClueWidget(clue.number, clue.direction, clue.references)
            clue_widget.selectClue.connect(self._handle_clue_click)
            clue_widget.setContentsMargins(0, 4, 0, 4)
            clue_widget.setStyleSheet("border-left: 8px solid; border-color: transparent;")
            clue_layout = QHBoxLayout()
            clue_layout.setContentsMargins(0, 0, 0, 0)
            clue_layout.setSpacing(0)

            clue_number = QLabel(str(clue.number), scroll_content)
            clue_number.setAlignment(Qt.AlignRight)
            clue_number.setFixedWidth(20)
            clue_font = QFont("Arial")
            clue_font.setBold(True)
            clue_number.setFont(clue_font)

            text_edit = CluesTextEdit(clue_widget)
            text_edit.setText(clue.text.strip())

            clue_layout.addSpacing(12)
            clue_layout.addWidget(clue_number)
            clue_layout.addSpacing(12)
            clue_layout.addWidget(text_edit)

            clue_widget.setLayout(clue_layout)
            clue_widget.setObjectName("clueRow")
            self.scroll_layout.addWidget(clue_widget)

            self.clues[(clue.number, clue.direction)] = clue_widget

            last_text_edit = text_edit

        parent_layout.addWidget(container)
        return last_text_edit

    def greyout_text(self, number: int, direction: str, make_grey: bool) -> None:
        key=(number, direction)
        clue = self.clues.get(key)
        if clue:
            clue.grey = "color: grey;" if make_grey else ""
            self.applyStyleSheet(clue)
            
    def grey_all_clues(self) -> None:
        for clue in self.clues.values():
            clue.grey = "color: grey;"
            self.applyStyleSheet(self.clues[clue])

    def highlight_clue(self, number: int, direction: str) -> None:
        """Highlight the requested clue and reset the previous one."""
        key = (number, direction)
        clue = self.clues.get(key)
        if key == self._highlighted_key:
            if clue:
                self._scroll_clue_into_view(direction, clue)
            return
        # get rid of the previously highligthed clue
        if self._highlighted_key and self._highlighted_key != self._side_highlighted_key:
            self.clues[self._highlighted_key].applyToAll = "border-left: 8px solid transparent; background-color: transparent;"
            self.clues[self._highlighted_key].applyToText = "background-color: transparent;"
            self.applyStyleSheet(self.clues[self._highlighted_key]) 

        # highlight the current clue
        if clue:
            clue.applyToAll =  "border-left: 8px solid #47c8ff; background-color: #47c8ff;"  
            clue.applyToText = "background-color: transparent;"
            self._highlighted_key = key
            self._scroll_clue_into_view(direction, clue)
            self.applyStyleSheet(clue)
        else:
            self._highlighted_key = None
        
    def applyStyleSheet(self, clue):
        string =  f"QWidget#clueRow {{ {clue.applyToAll}}}\nQWidget#clueRow * {{ {clue.applyToText} {clue.grey}}}" 
        print(string)
        clue.setStyleSheet(string)
    
    def clear_referenced_clues_highlight(self):
        for clue in self.referenced_clues:
            if clue != self.clues[self._highlighted_key] and clue != self.clues[self._side_highlighted_key]:
                clue.applyToAll = "border-left: 8px solid transparent; background-color: transparent; "
                self.applyStyleSheet(clue)
        self.referenced_clues.clear()
    

    def highlight_reference_clue(self, number: int, direction: str):
        key = (number, direction)
        clue = self.clues.get(key)
        if clue:
            self.referenced_clues.append(clue)
            clue.applyToAll = "border-left: 8px solid #baab04; background-color: #baab04; "           
            self.applyStyleSheet(clue)

    
    def highlight_clue_side(self, number: int, direction: str) -> None:
        key = (number, direction)
        sideBox = self.clues.get(key)

        if key == self._side_highlighted_key:
            if sideBox:
                self._scroll_clue_into_view(direction, sideBox)
            return

        if self._side_highlighted_key and self._side_highlighted_key != self._highlighted_key:
            #self.clues[self._side_highlighted_key].setStyleSheet(f"border-left: 8px solid; border-color: transparent; background-color: transparent;")
            self.clues[self._side_highlighted_key].applyToAll = "border-left: 8px solid transparent; background-color: transparent; "
            self.clues[self._side_highlighted_key].applyToText = "background-color: transparent;"
            self.applyStyleSheet(self.clues[self._side_highlighted_key])

        if sideBox:
            sideBox.applyToAll = "border-left: 8px solid #47c8ff; background-color: transparent;"
            sideBox.applyToText = "background-color: transparent;"
            self._side_highlighted_key = key
            self._scroll_clue_into_view(direction, sideBox)
            self.applyStyleSheet(sideBox)
        else:
            self._side_highlighted_key = None
        


    def _handle_clue_click(self, number: int, direction: str, references) -> None:
        """React to clue clicks by highlighting and bubbling the event."""
        self.clear_referenced_clues_highlight()
        self.highlight_clue(number, direction)
        for reference in references:
            self.highlight_reference_clue(reference["number"], reference["direction"])
        self.clue_selected.emit(number, direction)

    def _scroll_clue_into_view(self, direction: str, text_edit: CluesTextEdit) -> None:
        """Scroll the appropriate area so the clue appears at the top."""
        scroll_area = self._scroll_areas.get(direction.lower())
        if not scroll_area:
            return

        scrollbar = scroll_area.verticalScrollBar()
        if not scrollbar:
            return

        container = scroll_area.widget()
        if not container:
            return

        top_left = text_edit.mapTo(container, QPoint(0, 0))
        target_y = max(0, top_left.y())
        target = min(target_y, scrollbar.maximum())

        current = scrollbar.value()
        if current == target:
            return

        timer = getattr(scroll_area, "_scroll_timer", None)
        if timer and timer.isActive():
            timer.stop()

        duration_ms = 300
        interval_ms = 16
        steps = max(1, duration_ms // interval_ms)
        easing = QEasingCurve(QEasingCurve.OutCubic)
        step = 0

        timer = QTimer(scroll_area)

        def update_scroll():
            nonlocal step
            step += 1
            progress = min(1.0, step / steps)
            eased = easing.valueForProgress(progress)
            value = current + (target - current) * eased
            scrollbar.setValue(int(round(value)))
            if progress >= 1.0:
                timer.stop()
                scrollbar.setValue(target)
                scroll_area._scroll_timer = None

        timer.timeout.connect(update_scroll)
        scroll_area._scroll_timer = timer
        timer.start(interval_ms)
        update_scroll()


class ClueWidget(QWidget):
    selectClue = Signal(int, str, list)

    def __init__(self, number: int, direction: str, references):
        super().__init__()

        # without this the margins and the spacing does not get colored in with the background
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.applyToAll = ""
        self.applyToText = ""
        self.grey = ""
        self.number = number
        self.direction = direction
        self.references = references

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selectClue.emit(self.number, self.direction, self.references)
        super().mousePressEvent(event)
