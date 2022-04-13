from PyQt5.QtCore import pyqtSignal, QObject
from pyqtgraph.Point import Point
from mk_roi import *


class PlotSignal(QObject):
    plotSyncReceived = pyqtSignal(str, str, Point, Point)
    plotRemoveSyncReceived = pyqtSignal(str, str)
    roiSizeSyncReceived = pyqtSignal(str, str, float, float)
    roiClicked = pyqtSignal(float, float)
    hoveringReceived = pyqtSignal(SpecRoi)
    playTypeReceived = pyqtSignal(int, str, str)
