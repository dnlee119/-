import pyqtgraph as pg
from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import Qt, QPoint
from pyqtgraph.Qt import QtCore


class WaveLine(pg.InfiniteLine):
    def __init__(self):
        line_color = pg.mkPen(color=(150, 150, 150))
        line_hover_color = pg.mkPen(color=(0, 0, 0))
        super().__init__(pen=line_color, hoverPen=line_hover_color, angle=90, movable=True)


class WaveRoi(pg.LinearRegionItem):
    def __init__(self, start_point, size, num, signal):
        line_color = pg.mkPen(color=(240, 0, 0))
        line_hover_color = pg.mkPen(color=(0, 240, 0))
        super().__init__(values=(start_point, size), pen=line_color, hoverPen=line_hover_color)
        self.menu = QMenu()
        self.mk_ctrl_menu()

        self.roi_num = num
        self.main_signal = signal
        self.sigRegionChanged.connect(self.size_changed_fuc)

    def mk_ctrl_menu(self):
        self.menu.setContextMenuPolicy(Qt.CustomContextMenu)
        self.delAction = self.menu.addAction("지우기")
        self.quitAction = self.menu.addAction("닫기")
        self.delAction.triggered.connect(self.del_ctrl_fuc)

    def del_ctrl_fuc(self):
        self.main_signal.plotRemoveSyncReceived.emit("remove", self.roi_num)

    # Mouse Function Part
    def mouseClickEvent(self, e):
        if e.button() == QtCore.Qt.MouseButton.LeftButton:
            pos_s_x, pos_e_x = self.getRegion()
            self.main_signal.roiClicked.emit(pos_s_x, pos_e_x)
            self.main_signal.playTypeReceived.emit(1, "w", self.roi_num)
        elif e.button() == QtCore.Qt.MouseButton.RightButton:
            point = QPoint(int(e.screenPos()[0]), int(e.screenPos()[1]))
            self.menu.exec_(point)

    def hoverEvent(self, ev):
        hover = False
        if not ev.isExit():
            hover = True
        if hover:
            self.setMouseHover(True)
            self.main_signal.hoveringReceived.emit(self)
        else:
            self.setMouseHover(False)
            self.main_signal.hoveringReceived.emit(self)

    # RoI Control Part
    def size_changed_fuc(self, roi):
        pos_s_x, pos_e_x = roi.getRegion()
        self.main_signal.roiSizeSyncReceived.emit("tospec", self.roi_num, pos_s_x, pos_e_x)


class SpecRoi(pg.ROI):
    def __init__(self, start_point, size, num, signal):
        line_color = pg.mkPen(color=(240, 0, 0))
        line_hover_color = pg.mkPen(color=(0, 240, 0))
        handle_color = pg.mkPen(color=(255, 255, 255))
        super().__init__(pos=start_point, size=size, pen=line_color, hoverPen=line_hover_color,
                         handlePen=handle_color, invertible=True)
        self.addScaleHandle([0.5, 1], [0.5, 0])
        self.addScaleHandle([1, 1], [0, 0])
        self.addScaleHandle([0, 0], [1, 1])
        self.addScaleHandle([1, 0.5], [0.5, 0.5])
        self.addScaleHandle([0, 0.5], [0.5, 0.5])
        self.addScaleHandle([0.5, 0], [0.5, 1])

        self.menu = QMenu()
        self.mk_ctrl_menu()

        self.roi_num = num
        self.main_signal = signal
        self.sigRegionChanged.connect(self.size_changed_fuc)
        self.sigHoverEvent.connect(self.main_signal.hoveringReceived.emit)

    def mk_ctrl_menu(self):
        self.menu.setContextMenuPolicy(Qt.CustomContextMenu)
        self.delAction = self.menu.addAction("지우기")
        self.quitAction = self.menu.addAction("닫기")
        self.delAction.triggered.connect(self.del_ctrl_fuc)

    def del_ctrl_fuc(self):
        self.main_signal.plotRemoveSyncReceived.emit("remove", self.roi_num)

    # Mouse Function Part
    def mouseClickEvent(self, e):
        if e.button() == QtCore.Qt.MouseButton.LeftButton:
            pos_s_x, pos_e_x = self.pos().x(), self.size().x() + self.pos().x()
            if pos_s_x > pos_e_x:
                tmp = pos_s_x
                pos_s_x = pos_e_x
                pos_e_x = tmp
            self.main_signal.roiClicked.emit(pos_s_x, pos_e_x)
            self.main_signal.playTypeReceived.emit(1, "s", self.roi_num)
        elif e.button() == QtCore.Qt.MouseButton.RightButton:
            point = e.screenPos().toQPoint()
            self.menu.exec_(point)

    def hoverEvent(self, ev):
        hover = False
        if not ev.isExit():
            hover = True
        if hover:
            self.setMouseHover(True)
            self.sigHoverEvent.emit(self)
        else:
            self.setMouseHover(False)
            self.sigHoverEvent.emit(self)

    # RoI Control Part
    def size_changed_fuc(self, roi):
        pos_s_x, pos_e_x = roi.pos().x(), roi.size().x() + roi.pos().x()
        self.main_signal.roiSizeSyncReceived.emit("towave", self.roi_num, pos_s_x, pos_e_x)
