import time

import pyqtgraph as pg
from pyqtgraph.Point import Point
from mk_roi import SpecRoi, WaveRoi, WaveLine
from pyqtgraph.Qt import QtCore, QtGui


class WavePlots(pg.PlotWidget):
    def __init__(self, sound_time, sample_rate, player, signal):
        super().__init__()
        self.sound_time = sound_time
        self.sample_rate = sample_rate
        self.player = player
        self.main_signal = signal
        self.hover = False

        self.x_length = 150
        self.y_length = 180

        self._plotViewBox = self.getViewBox()
        self.graph_setting()
        self.size_refresh()

        self.lines = WaveLine()
        self.addItem(self.lines)
        self.scene().sigMouseClicked.connect(self.mouseClick)
        self.main_signal.hoveringReceived.connect(self.hovering_fuc)

    def graph_setting(self):
        self._plotViewBox.state["mouseEnabled"] = [False, False]
        self._plotViewBox.state["enableMenu"] = False
        self._plotViewBox.state["wheelScaleFactor"] = 0
        self._plotViewBox.mouseDragEvent = self.mouseDragEvent
        self.setLabel("left", "   ")
        self.setXRange(0, self.sound_time, padding=0)
        self.setYRange(-1.000, 1.000, padding=0)
        self.setLimits(xMin=0, yMin=0.01)
        self.setBackground("w")

    def size_refresh(self):
        self.resize(int(self.x_length * self.sound_time), self.y_length)
        self._plotViewBox.setBackgroundColor((255, 255, 255))
        zoom_level = int((self.x_length - 50) / 100)
        if zoom_level < 4:
            self.getPlotItem().getAxis("bottom").setTickSpacing(1, 0.2)
        elif zoom_level < 7:
            self.getPlotItem().getAxis("bottom").setTickSpacing(0.5, 0.1)
        elif zoom_level < 10:
            self.getPlotItem().getAxis("bottom").setTickSpacing(0.1, 0.02)
        else:
            self.getPlotItem().getAxis("bottom").setTickSpacing(0.05, 0.01)

    # Mouse Function Part
    def mouseClick(self, e):
        if e.button() == QtCore.Qt.MouseButton.LeftButton and not self.hover:
            e.accept()
            new_pos = self._plotViewBox.mapSceneToView(e.scenePos())
            self.lines.setPos([new_pos.x(), 0])
            in_time = self.lines.pos().x()
            self.player.setPosition(round(in_time * 1000))
            self.main_signal.playTypeReceived.emit(0, "l", "")

    def mouseDragEvent(self, e, axis=None):
        e.accept()
        current_pos = e.scenePos()
        start_pos = e.buttonDownScenePos()
        current_point = self._plotViewBox.mapSceneToView(current_pos)
        start_point = self._plotViewBox.mapSceneToView(start_pos)
        if e.button() == QtCore.Qt.MouseButton.LeftButton:
            if e.isFinish():
                if abs(start_point.x() - current_point.x()) < 0.05 or abs(start_point.y() - current_point.y()) < 0.1:
                    self._plotViewBox.rbScaleBox.hide()
                else:
                    roi_id = str(time.time()).replace(".", "")
                    globals()["w{}".format(roi_id)] = WaveRoi(start_point.x(), current_point.x(), roi_id, self.main_signal)
                    self._plotViewBox.addItem(globals()["w{}".format(roi_id)])
                    self._plotViewBox.rbScaleBox.hide()
                    self.main_signal.plotSyncReceived.emit("tospec", roi_id, current_pos, start_pos)
            else:
                self.update_scale_box(e.buttonDownScenePos(), e.scenePos())

    def update_scale_box(self, p1, p2):
        r = QtCore.QRectF(p1, p2)
        r = self._plotViewBox.childGroup.mapRectFromScene(r)
        self._plotViewBox.rbScaleBox.setPos(r.topLeft())
        tr = QtGui.QTransform.fromScale(r.width(), r.height())
        self._plotViewBox.rbScaleBox.setTransform(tr)
        self._plotViewBox.rbScaleBox.show()

    def hovering_fuc(self, roi):
        self.hover = roi.mouseHovering

    def wheelEvent(self, e):
        pass

    # RoI Control Part
    def mk_roi_sync_fuc(self, roi_id, point1, point2):
        current_point = self._plotViewBox.mapSceneToView(point1)
        start_point = self._plotViewBox.mapSceneToView(point2)
        globals()["w{}".format(roi_id)] = WaveRoi(start_point.x(), current_point.x(), roi_id, self.main_signal)
        self._plotViewBox.addItem(globals()["w{}".format(roi_id)])

    def roi_change_fuc(self, roi_num, pos_s_x, pos_e_x):
        globals()["w{}".format(roi_num)].setRegion(Point(pos_s_x, pos_e_x))

    def remove_roi_fuc(self, name):
        self._plotViewBox.removeItem(globals()["w{}".format(name)])
        del globals()["w{}".format(name)]

    def return_pos(self, roi_id):
        return globals()["w{}".format(roi_id)].getRegion()


class SpecPlots(pg.PlotWidget):
    def __init__(self, sound_time, sample_rate, player, signal):
        super().__init__()
        self.sound_time = sound_time
        self.sample_rate = sample_rate
        self.player = player
        self.main_signal = signal
        self.hover = False

        self.x_length = 150
        self.y_length = 180

        self._plotViewBox = self.getViewBox()
        self._plotViewBox.setAutoVisible(x=True, y=True)
        self.graph_setting()
        self.size_refresh()

        self.img = pg.ImageItem()
        self.addItem(self.img)

        self.lines = WaveLine()
        self.addItem(self.lines)
        self.scene().sigMouseClicked.connect(self.mouseClick)
        self.main_signal.hoveringReceived.connect(self.hovering_fuc)

    def graph_setting(self):
        self._plotViewBox.state["mouseEnabled"] = [False, False]
        self._plotViewBox.state["enableMenu"] = False
        self._plotViewBox.state["wheelScaleFactor"] = 0
        self._plotViewBox.mouseDragEvent = self.mouseDragEvent
        self.setXRange(0, self.sound_time, padding=0)
        self.setLimits(xMin=0, yMin=0, yMax=self.sample_rate)
        self.setBackground("w")

    def size_refresh(self):
        self.resize(int(self.x_length * self.sound_time), self.y_length)
        zoom_level = int((self.x_length - 50) / 100)
        if zoom_level < 4:
            self.getPlotItem().getAxis("bottom").setTickSpacing(1, 0.2)
        elif zoom_level < 7:
            self.getPlotItem().getAxis("bottom").setTickSpacing(0.5, 0.1)
        elif zoom_level < 10:
            self.getPlotItem().getAxis("bottom").setTickSpacing(0.1, 0.02)
        else:
            self.getPlotItem().getAxis("bottom").setTickSpacing(0.05, 0.01)

    # Mouse Function Part
    def mouseClick(self, e):
        if e.button() == QtCore.Qt.MouseButton.LeftButton and not self.hover:
            e.accept()
            new_pos = self._plotViewBox(e.scenePos())
            self.lines.setPos([new_pos.x(), 0])
            in_time = self.lines.pos().x()
            self.player.setPosition(round(in_time * 1000))
            self.main_signal.playTypeReceived.emit(0, "l", "")

    def mouseDragEvent(self, e, axis=None):
        e.accept()
        current_pos = e.scenePos()
        start_pos = e.buttonDownScenePos()
        current_point = self._plotViewBox.mapSceneToView(current_pos)
        start_point = self._plotViewBox.mapSceneToView(start_pos)
        if start_point.x() > current_point.x():
            tmp = start_point
            start_point = current_point
            current_point = tmp
        size_ = current_point - start_point
        if e.button() == QtCore.Qt.MouseButton.LeftButton:
            if e.isFinish():
                if (abs(size_.x()) < 0.05) or (abs(size_.y()) < 1000):
                    self._plotViewBox.rbScaleBox.hide()
                else:
                    roi_id = str(time.time()).replace(".", "")
                    globals()["s{}".format(roi_id)] = SpecRoi(start_point, size_, roi_id, self.main_signal)
                    self._plotViewBox.addItem(globals()["s{}".format(roi_id)])
                    self._plotViewBox.rbScaleBox.hide()
                    self.main_signal.plotSyncReceived.emit("towave", roi_id, current_pos, start_pos)
            else:
                self.update_scale_box(e.buttonDownScenePos(), e.scenePos())

    def update_scale_box(self, p1, p2):
        r = QtCore.QRectF(p1, p2)
        r = self._plotViewBox.childGroup.mapRectFromScene(r)
        self._plotViewBox.rbScaleBox.setPos(r.topLeft())
        tr = QtGui.QTransform.fromScale(r.width(), r.height())
        self._plotViewBox.rbScaleBox.setTransform(tr)
        self._plotViewBox.rbScaleBox.show()

    def hovering_fuc(self, roi):
        self.hover = roi.mouseHovering

    # RoI Control Part
    def mk_roi_sync_fuc(self, roi_id, point1, point2):
        current_point = self._plotViewBox.mapSceneToView(point1)
        start_point = self._plotViewBox.mapSceneToView(point2)
        size_ = current_point - start_point
        globals()["s{}".format(roi_id)] = SpecRoi(start_point, size_, roi_id, self.main_signal)
        self._plotViewBox.addItem(globals()["s{}".format(roi_id)])

    def roi_change_fuc(self, roi_num, pos_s_x, pos_e_x):
        roi_pos_y = globals()["s{}".format(roi_num)].pos().y()
        roi_size_y = globals()["s{}".format(roi_num)].size().y()
        roi_size_x = pos_e_x - pos_s_x
        globals()["s{}".format(roi_num)].setPos(Point(pos_s_x, roi_pos_y))
        globals()["s{}".format(roi_num)].setSize(Point(roi_size_x, roi_size_y))

    def remove_roi_fuc(self, name):
        self._plotViewBox.removeItem(globals()["s{}".format(name)])
        del globals()["s{}".format(name)]

    def return_pos(self, roi_id):
        pos = globals()["s{}".format(roi_id)].pos()
        size = globals()["s{}".format(roi_id)].size()
        return pos, size

    def wheelEvent(self, e):
        pass