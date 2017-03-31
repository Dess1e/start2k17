"""Scene sets here."""
# coding=utf-8

from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtCore import QTimer


class Scene(QGraphicsScene):
    __TIMER_DELAY = 20

    PAUSE = 'pause'
    CLEAR = 'clear'
    SAVE = 'save'
    COMBINE = 'combine'

    def __init__(self, *args):
        super().__init__(*args)
        # Layout buffer
        self.__sceneStack = []
        # Show when game on pause
        self.__paused = False
        self.__timer = None

        self.initTimer()

    @property
    def layout(self):
        return self.__sceneStack[-1]

    def initTimer(self):
        self.__timer = QTimer(self)

        self.__timer.timeout.connect(self.__update)

        self.__timer.start(self.__TIMER_DELAY)

    def __update(self):
        """Updates current scene."""
        try:
            currentScene = self.__sceneStack[-1]
        except IndexError:
            return

        # If this is game layout, update all
        if isinstance(currentScene, tuple):
            for layout in currentScene:
                layout.update()

        currentScene.update()

    def resizeLayouts(self):
        """Resizes layouts in buffer.

        Primarily used when resolution changed =)
        """
        for layout in self.__sceneStack:
            if isinstance(layout, tuple):
                    for _layout in layout:
                        _layout.prepareGeometry()

            layout.prepareGeometry()

    def clearBuffer(self):
        for layout in self.__sceneStack:
            if isinstance(layout, tuple):
                for _layout in layout:
                    _layout.hide()
            layout.hide()

    def nextLayout(self, layout, switchType=None):
        switchType = switchType or self.CLEAR

        if len(self.__sceneStack):
            if switchType == self.PAUSE:
                self.__timer.stop()

                self.__paused = True

                self.__sceneStack[-1].pause()
            elif switchType == self.SAVE:
                self.__sceneStack[-1].hide()
            elif switchType == self.COMBINE:
                curScene = self.__sceneStack.pop()
                layout = (curScene, layout)
            else:
                try:
                    self.__sceneStack.pop().hide()
                except IndexError:
                    pass

        self.__sceneStack.append(layout)
        layout.show()

    def prevLayout(self):
        currentScene = self.__sceneStack.pop()
        currentScene.hide()

        if self.__paused:
            self.__paused = False
            self.__timer.start()

            self.__sceneStack[-1].resume()
        else:
            self.__sceneStack[-1].show()
