"""Layout like layouts in qt(QGridLayout)."""
# coding=utf-8

from abc import ABCMeta, abstractmethod
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsItem


class Layout(metaclass=ABCMeta):
    """Base layout class(For inheritance only)."""

    def __init__(self, scene: QGraphicsScene):
        self._scene = scene
        self._view = scene.views()[0]

        self._width, self._height = self._view.width(), self._view.height()
        # Keeps all items in layout
        self.__items = []
        # State of layout
        self.__pause = False
        # Parent item for group
        self.__rootItem = None

    @abstractmethod
    def addItem(self):
        pass

    @abstractmethod
    def show(self):
        """Add items to scene."""
        pass

    @abstractmethod
    def hide(self):
        """Remove items from scene."""
        pass

    def prepareGeometry(self):
        self._width, self._height = self._view.widht(), self._view.height()

    def pause(self):
        pass

    def update(self):
        """Updates all items in layout."""
        pass


class GridLayout(Layout):
    """Grid layout for managing simple menus."""

    # Dummy item
    DUMMY = ''

    def __init__(self, scene: QGraphicsScene):
        super().__init__(scene)
        self._scene = scene

        self.__rectWidth, self.__rectHeight = None, None

        self.rows, self.colls = 1, 1
        # items == [[(item, rowspan, colspan)]]
        self.items = [[]]
        print(self._width, self._height)
        print(self._view.sceneRect())

    def hasItem(self):
        for row in self.items:
            for item, _, _ in row:
                if item != self.DUMMY:
                    return True

        return False

    def addItem(self, item: QGraphicsItem, row, coll, rowspan=1, colspan=1):
        if item != self.DUMMY:
            if not self.hasItem():
                self.__rootItem = item
                self.__rootItem.setParentItem(None)
            else:
                item.setParentItem(self.__rootItem)

        self.rows = self.rows if row + rowspan <= self.rows else row + 1
        self.colls = self.colls if coll + colspan <= self.colls else coll + 1
        self.resize()

        self.items[row][coll] = (item, rowspan, colspan)
        self.repaint()

    def resize(self):
        """Fill item matrix to fit in all colls and rows."""
        for x in range(self.rows + 1 - len(self.items)):
            self.items.append([])

        for row in range(len(self.items)):
            for y in range(self.colls - len(self.items[row])):
                self.items[row].append((self.DUMMY, 1, 1))

        self.__rectWidth = self._width / self.colls
        self.__rectHeight = self._height / self.rows

    def repaint(self):
        """Redraws all widgets after new added and matrix resized."""
        from math import sqrt

        for row in range(self.rows):
            for coll in range(self.colls):
                item, rspan, cspan = self.items[row][coll]

                if item == self.DUMMY:
                    continue

                rect = item.boundingRect()

                if item.resizable:
                    cx, cy = rect.width() / 2, rect.height() / 2
                    rx, ry = rect.x(), rect.y()

                    rx = cx - sqrt(self.__rectWidth) * 3.5  # / 2
                    ry = cy - sqrt(self.__rectHeight) * 2  # / 2

                    item.moveBy(rx, ry)

                    width = sqrt(self.__rectWidth) * 7
                    height = sqrt(self.__rectHeight) * 4

                    item.setBoundingRect(0, 0, width, height)
                else:
                    width, height = rect.width(), rect.height()

                # Center of scene rect in which we will place widget
                sceneX = self.__rectWidth * coll + self.__rectWidth * cspan / 2
                sceneY = (self.__rectHeight * row +
                          self.__rectHeight * rspan / 2)

                # Center of widget bounding rect
                x = sceneX - width / 2
                y = sceneY - height / 2

                # We need to shift item coords because of itemGroup
                # Fucking itemGroup in qt shifts all coords by parent coords
                # FUCK!!
                x = x - self.__rootItem.x() if item != self.__rootItem else x
                y = y - self.__rootItem.y() if item != self.__rootItem else y

                item.setPos(x, y)

    def show(self):
        # Here, at last, we can use the benefits of item group
        self._scene.addItem(self.__rootItem)

    def hide(self):
        # Here too
        self._scene.removeItem(self.__rootItem)
