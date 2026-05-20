from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QLayoutItem


class FlowLayout(QLayout):
    """
    Simple flow layout.

    Widgets are positioned left-to-right and wrap to the next line
    when there is no more horizontal space.
    """

    def __init__(self, parent=None, margin: int = 0, hspacing: int = 20, vspacing: int = 20):
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self._hspacing = hspacing
        self._vspacing = vspacing
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item: QLayoutItem) -> None:
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def horizontalSpacing(self) -> int:
        return self._hspacing

    def verticalSpacing(self) -> int:
        return self._vspacing

    def _do_layout(self, rect: QRect, test_only: bool = False) -> int:
        x = rect.x()
        y = rect.y()
        line_height = 0

        for item in self._items:
            item_size = item.sizeHint()
            space_x = self.horizontalSpacing()
            space_y = self.verticalSpacing()

            next_x = x + item_size.width() + space_x

            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y += line_height + space_y
                next_x = x + item_size.width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item_size))

            x = next_x
            line_height = max(line_height, item_size.height())

        return y + line_height - rect.y()