"""Layout like layouts in qt(QGridLayout)."""
# coding=utf-8

from logging import getLogger, INFO, DEBUG
from abc import ABCMeta, abstractmethod

from PyQt5.QtWidgets import QGraphicsScene, QGraphicsItem
from PyQt5.QtGui import QImage

from objects.map_elements import Wall, Air, BackgroundImage



L = getLogger('gameLogger')


class Layout(metaclass=ABCMeta):
    """Base layout class(For inheritance only)."""

    def __init__(self, scene: QGraphicsScene):
        """
        Initialization of layout.

        Call to prepareGeomety must be done by child,
        only after all vars for resize and repaint methods initialized!
        """
        self.__scene = scene
        self.__view = scene.views()[0]
        # State of layout
        self.hided = True
        # Parent item for grouping self._rootItem = None
        # Parent item for grouping
        self._rootItem = None

    @property
    def scene(self):
        return self.__scene

    @property
    def view(self):
        return self.__view

    @abstractmethod
    def addItem(self):
        pass

    @abstractmethod
    def resize(self):
        """Resizes internal buffer and cell rect."""
        pass

    @abstractmethod
    def repaint(self):
        """Redraws widgets on layout."""
        pass

    def show(self):
        """Add items to scene."""
        if not self.hided:
            L.debug('\u001b[34mSkipping showing in {}\u001b[0m'.format(self))
            return
        L.debug('\u001b[32mhided = False in {}\u001b[0m'.format(self))
        self.hided = False

    def hide(self):
        """Remove items from scene."""
        if self.hided:
            L.debug('\u001b[34mSkipping hiding in {}\u001b[0m'.format(self))
            return
        L.debug('\u001b[32mhided = True in {}\u001b[0m'.format(self))
        self.hided = True

    def prepareGeometry(self):
        """Prepare scene to resolution changes.

        In fact, not only preparing, but updating too.
        """
        self._width, self._height = self.view.resolution
        self.scene.setSceneRect(0, 0, *self.view.resolution)
        # To avoid image artifacts
        self.update()

    def pause(self):
        L.debug('\u001b[34mPausing layout\u001b[0m')

    def resume(self):
        L.debug('\u001b[34mResuming layout\u001b[0m')

    def update(self):
        """Updates all items in layout.

        Not needed in menu, for entity layouts.
        """
        self.repaint()


class GridLayout(Layout):
    """Grid layout for managing simple menus."""

    # Dummy item for resizing purposes
    DUMMY = ''

    def __init__(self, scene: QGraphicsScene, background=False):
        super().__init__(scene)
        L.debug('\u001b[33mInitializing grid layout\u001b[0m')
        self.__rectWidth, self.__rectHeight = None, None
        self.rows, self.colls = 1, 1
        # items: [[(item, rowspan, colspan)]]
        self._items = [[]]
        # Initialization of width and height
        self.prepareGeometry()

        if background:
            self.setBackground()

    def prepareGeometry(self):
        self._width, self._height = self.view.resolution
        self.scene.setSceneRect(0, 0, *self.view.resolution)

        self.resize()
        self.update()

    def setBackground(self):
        self.scene.nextLayout(Background)
        self.scene.nextLayout(self, mode=self.scene.COMBINE)

    def addItem(self, item: QGraphicsItem, row, coll, rowspan=1, colspan=1):
        if item != self.DUMMY:
            L.debug('\u001b[34mAdding {} in row {}, col {}\u001b[0m'.format(item, row, coll))
            if self._rootItem is None:
                self._rootItem = item
                self._rootItem.setParentItem(None)
            else:
                item.setParentItem(self._rootItem)

        self.rows = self.rows if row + rowspan <= self.rows else row + 1
        self.colls = self.colls if coll + colspan <= self.colls else coll + 1
        self.resize()

        self._items[row][coll] = (item, rowspan, colspan)
        self.repaint()

    def resize(self):
        for x in range(self.rows + 1 - len(self._items)):
            self._items.append([])

        for row in range(len(self._items)):
            for y in range(self.colls - len(self._items[row])):
                self._items[row].append((self.DUMMY, 1, 1))

        self.__rectWidth = self._width / self.colls
        self.__rectHeight = self._height / self.rows

    def repaint(self):
        from math import sqrt

        for row in range(self.rows):
            for coll in range(self.colls):
                item, rspan, cspan = self._items[row][coll]

                if item == self.DUMMY:
                    continue

                rect = item.boundingRect()
                e = item.expandable

                if item.resizable or e:
                    cx, cy = rect.width() / 2, rect.height() / 2
                    rx, ry = rect.x(), rect.y()

                    rx = cx - self.__rectWidth if e else cx - sqrt(self.__rectWidth) * 3.5
                    ry = cy - self.__rectHeight / 2 if e else cy - sqrt(self.__rectHeight) * 2

                    item.moveBy(rx, ry)

                    width = self.__rectWidth if e else sqrt(self.__rectWidth) * 7
                    height = self.__rectHeight if e else sqrt(self.__rectHeight) * 4

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
                x = x - self._rootItem.x() if item != self._rootItem else x
                y = y - self._rootItem.y() if item != self._rootItem else y

                item.setPos(x, y)

    def show(self):
        super().show()
        # Here, at last, we can use the benefits of item group
        L.debug('\u001b[34mAdding {} to scene\u001b[0m'.format(self))
        self.scene.addItem(self._rootItem)

    def hide(self):
        super().hide()
        # Here too
        L.debug('\u001b[34mRemoving {} from scene\u001b[0m'.format(self))
        self.scene.removeItem(self._rootItem)


class Background(GridLayout):
    def __init__(self, scene, opacity=1, path=None):
        super().__init__(scene)
        L.debug('\u001b[33mInitializing Background\u001b[0m')
        self.opacity = opacity
        L.debug('\u001b[32mOpacity = {}\u001b[0m'.format(opacity))
        path = path or self.getPath()
        L.debug('\u001b[32mBackground = {}\u001b[0m'.format(path))
        self.image = QImage(path)

        self.fillBackground()

    def getPath(self):
        from os import listdir, sep
        from random import choice

        images = listdir('backgrounds')

        return 'backgrounds' + sep + choice(images)

    def fillBackground(self):
        self.addItem(BackgroundImage(self.image, self.opacity), 0, 0)


class Map(GridLayout):
    # Mapping between symbols in file and game objects
    MAPPING = {'w': Wall, 'e': Air}

    def __init__(self, scene, map):
        super().__init__(scene)
        L.debug('\u001b[34mInitializing Map\u001b[0m')
        L.debug('\u001b[32mmap = {}\u001b[0m'.format(map))

        L.debug('\u001b[34mConnecting openMenu to esc\u001b[0m')
        self.view.escPressed.connect(self.openMenu)

        self.parseMap(map)

    def openMenu(self):
        from gui.menus import InGameMenu

        wrap = self.scene.wrap
        nextLayout = self.scene.nextLayout

        nextLayout(wrap({Background: (), InGameMenu: ()}), mode=self.scene.PAUSE)

    def parseMap(self, mapfile):
        L.debug('\u001b[34mParsing map file\u001b[0m')
        L.setLevel(INFO)
        mapFile = open(mapfile, 'r')

        skipped = 0
        for row, line in enumerate(mapFile):
            # Skip comment lines
            if line.startswith('#'):
                skipped += 1
                continue

            for col, sym in enumerate(line):
                try:
                    item = self.MAPPING[sym]()
                except KeyError:
                    continue
                self.addItem(item, row - skipped, col)
        L.setLevel(DEBUG)
        L.debug('\u001b[32mFile map parsed\u001b[0m')
        mapFile.close()

    def pause(self):
        super().pause()

        L.debug('\u001b[34mDisconnecting openMenu from esc\u001b[0m')
        self.view.escPressed.disconnect(self.openMenu)

    def resume(self):
        super().resume()

        L.debug('\u001b[34mConnecting openMenu to esc\u001b[0m')
        self.view.escPressed.connect(self.openMenu)
