import sys

from scipy.signal import butter, filtfilt
import numpy as np
import soundfile as sf
from librosa import load, stft, amplitude_to_db, feature
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from mk_signal import PlotSignal
from mk_plot import *
from ConcatDialog import ConcatDialog
from DivideDialog import DivideDialog


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        _ui = "./UI/main.ui"
        uic.loadUi(_ui, self)
        # Set Variable
        self.player = QMediaPlayer()
        self.timer = QTimer()
        self.main_signal = PlotSignal()
        self.wave_widget = None
        self.spec_widget = None

        self.current_sound_data = []
        self.current_sound_sr = 0
        self.sound_time = 0
        self.current_file_name = ""
        self.player_type = ""
        self.spec_color_name = "inferno"
        self.x_zoom_int = 0
        self.y_zoom_int = 0
        self.play_speed_float = 1.0
        self.state = {"line_range": [], "playtype": 0, "roi_data": {}, "current_roi": "", "current_roi_type": ""}
        # playtype = 0:전체 실행, 1:부분 실행
        # roi_data = "roi_num": {"index": int, "pos_s_x" = float, "pos_e_x" = float}

        # Start Initiating
        self.loading_fuc()
        self.show()

    # Initiating Part
    def loading_fuc(self):
        self.ui_init()
        self.function_init()
        self.button_init()
        self.setting_init()

    def ui_init(self):
        _qr = self.frameGeometry()
        _cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        _qr.moveCenter(_cp)
        self.move(_qr.topLeft())

    def function_init(self):
        # Variables Created to the Designer
        # ui function setting
        self.scrollArea.horizontalScrollBar().valueChanged.connect(self.scrollbar_synchro_fuc)
        self.scrollArea_2.horizontalScrollBar().valueChanged.connect(self.scrollbar_2_synchro_fuc)
        # File Menu
        self.actionOpen.triggered.connect(self.load_file_fuc)
        self.actionSave.triggered.connect(self.save_file_fuc)
        self.actionClose.triggered.connect(self.close)
        # View Menu
        self.actionZoomInX.triggered.connect(self.zoom_in_x_fuc)
        self.actionZoomInX.setShortcut(QKeySequence("F1"))
        self.actionZoomOutX.triggered.connect(self.zoom_out_x_fuc)
        self.actionZoomOutX.setShortcut(QKeySequence("F2"))
        self.actionZoomInY.triggered.connect(self.zoom_in_y_fuc)
        self.actionZoomInY.setShortcut(QKeySequence("F3"))
        self.actionZoomOutY.triggered.connect(self.zoom_out_y_fuc)
        self.actionZoomOutY.setShortcut(QKeySequence("F4"))
        self.actionZoomRollback.triggered.connect(self.zoom_rollback_fuc)
        self.actionInferno.triggered.connect(lambda x: self.spec_color_set_fuc("inferno"))
        self.actionBinary.triggered.connect(lambda x: self.spec_color_set_fuc("binary_r"))
        self.actionCET.triggered.connect(lambda x: self.spec_color_set_fuc("CET-R4"))
        self.actionWaveForm.toggled.connect(self.wave_widget_hide_and_show_fuc)
        self.actionSpectrogram.toggled.connect(self.spec_widget_hide_and_show_fuc)
        # Edit Menu
        # self.actionReturn.triggered.connect(self.return_fuc)
        self.actionAddSound.triggered.connect(self.add_sound_main_fuc)
        self.actionCutSound.triggered.connect(self.cut_sound_main_fuc)
        self.actionSilenceSound.triggered.connect(self.silence_sound_main_fuc)
        self.actionCutSpectrogram.triggered.connect(self.cut_spectrogram_main_fuc)
        # Tools Menu
        self.actionFileConcat.triggered.connect(self.file_concat_dialog_fuc)
        self.actionFileDivide.triggered.connect(self.file_divide_dialog_fuc)
        # Play Menu
        self.actionPlay.triggered.connect(self.play_sound_fuc)
        self.actionPause.triggered.connect(self.pause_sound_fuc)
        self.actionStop.triggered.connect(self.stop_sound_fuc)
        self.actionPlaySpeedUp.triggered.connect(self.play_speed_up_fuc)
        self.actionPlaySpeedDown.triggered.connect(self.play_speed_down_fuc)
        self.actionPlaySpeedRollback.triggered.connect(self.play_speed_rollback_fuc)

        # Variables Created to the File
        self.timer.timeout.connect(self.update)
        self.main_signal.plotSyncReceived.connect(self.mk_roi_to)
        self.main_signal.plotRemoveSyncReceived.connect(self.roi_remove_fuc)
        self.main_signal.roiSizeSyncReceived.connect(self.roi_size_fuc)
        self.main_signal.roiClicked.connect(self.roi_clicked_fuc)
        self.main_signal.playTypeReceived.connect(self.play_type_change)

    def button_init(self):
        # Button Setting to Connect to Action
        # View Menu
        self.zoomInXButton.clicked.connect(self.actionZoomInX.trigger)
        self.zoomOutXButton.clicked.connect(self.actionZoomOutX.trigger)
        self.zoomInYButton.clicked.connect(self.actionZoomInY.trigger)
        self.zoomOutYButton.clicked.connect(self.actionZoomOutY.trigger)
        self.zoomRollbackButton.clicked.connect(self.actionZoomRollback.trigger)
        # Play Menu
        self.playButton.clicked.connect(self.actionPlay.trigger)
        self.pauseButton.clicked.connect(self.actionPause.trigger)
        self.stopButton.clicked.connect(self.actionStop.trigger)

    def setting_init(self):
        self.setAcceptDrops(True)
        self.timer.start(1)

    # Set State Function Part
    def play_type_change(self, type_num, roi_type, roi_num):
        self.state["playtype"] = type_num
        self.state["current_roi_type"] = roi_type
        self.state["current_roi"] = roi_num

    # Overriding Function Part
    def update(self):
        if self.player.state() == QMediaPlayer.PlayingState and self.state["playtype"] == 0:
            in_time = self.player.position() / 1000
            self.wave_widget.lines.setPos([in_time, 0])
            self.spec_widget.lines.setPos([in_time, 0])
        elif self.player.state() == QMediaPlayer.PlayingState and self.state["playtype"] == 1:
            in_time = self.player.position() / 1000
            if self.state["line_range"][0] <= in_time <= self.state["line_range"][1]:
                self.wave_widget.lines.setPos([in_time, 0])
                self.spec_widget.lines.setPos([in_time, 0])
            else:
                self.stop_sound_fuc()
        if self.state["current_roi_type"] == "s":
            self.actionCutSpectrogram.setEnabled(True)
        else:
            self.actionCutSpectrogram.setEnabled(False)

    def dragEnterEvent(self, e):
        if ".wav" in e.mimeData().urls()[0].toString():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        if ".wav" in e.mimeData().urls()[0].toString():
            e.accept()
            self.current_file_name = e.mimeData().urls()[0].toLocalFile()
            self.draw_plot(self.current_file_name)
        else:
            e.ignore()

    def closeEvent(self, e):
        ret = QtWidgets.QMessageBox.question(self, "종료?", "종료 하시겠습니까?",
                                             QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No)
        if ret == QtWidgets.QMessageBox.Yes:
            e.accept()
        else:
            e.ignore()

    # Function Part
    # Plotting Function Part
    def load_file_fuc(self):
        filter_ = "(*.wav)"
        self.current_file_name = QtWidgets.QFileDialog.getOpenFileName(self, '파일 선택', filter=filter_)[0]
        if self.current_file_name:
            self.draw_plot(self.current_file_name)
            
    def save_file_fuc(self):
        filter_ = "(*.wav)"
        save_name = QtWidgets.QFileDialog.getSaveFileName(self, "저장", self.current_file_name,
                                                                       filter=filter_)[0]
        sf.write(save_name, self.current_sound_data, samplerate=self.current_sound_sr)
        self.current_file_name = save_name

    def draw_plot(self, file_name):
        # load sound data
        self.current_sound_data, self.current_sound_sr = sf.read(file_name)
        self.setting_time_fuc()
        if self.current_sound_data.ndim == 2:
            self.current_sound_data = self.current_sound_data.mean(axis=1)

        self.draw_wavefrom_plot_fuc()
        self.draw_spectrogram_plot_fuc()
        self.plotting_init(0, 0)

    def setting_time_fuc(self):
        self.sound_time = len(self.current_sound_data) / self.current_sound_sr

    def draw_wavefrom_plot_fuc(self):
        pen_set = pg.mkPen(color=(0, 0, 240))
        self.wave_widget = WavePlots(self.sound_time, self.current_sound_sr, self.player, self.main_signal)
        time_data = np.arange(0, int(self.sound_time) + 1, (1.0 / self.current_sound_sr))[:len(self.current_sound_data)]
        self.wave_widget.plot(time_data, self.current_sound_data, pen=pen_set)
        self.scrollArea.setWidget(self.wave_widget)

    def draw_spectrogram_plot_fuc(self):
        n_fft_per = 1024
        hop_length_per = 64
        stft_result = stft(self.current_sound_data, n_fft=n_fft_per, hop_length=hop_length_per)
        D = np.abs(stft_result)
        D = feature.melspectrogram(S=D)
        spec_data = amplitude_to_db(D, ref=np.max).T
        freq = np.arange((hop_length_per / 2) + 1) / (float(hop_length_per) / self.current_sound_sr)
        yscale = 1.0 / (spec_data.shape[1] / freq[-1])
        self.spec_widget = SpecPlots(self.sound_time, self.current_sound_sr, self.player, self.main_signal)
        self.spec_widget.img.setImage(spec_data)
        self.spec_widget.img.scale((1./self.current_sound_sr) * hop_length_per, yscale)
        self.scrollArea_2.setWidget(self.spec_widget)

    def plotting_init(self, x_zoom, y_zoom):
        self.x_zoom_int = x_zoom
        self.y_zoom_int = y_zoom
        self.draw_plot_button_set_fuc()
        self.spec_color_set_fuc(self.spec_color_name)
        self.mk_play_line_set_fuc()
        self.set_to_player(self.current_file_name)
        self.zoom_screen_fuc()

    def draw_plot_button_set_fuc(self):
        # Action Setting
        # File Actions Set
        self.actionSave.setEnabled(True)
        # Edit Actions Set
        self.actionAddSound.setEnabled(True)
        self.actionCutSound.setEnabled(True)
        self.actionSilenceSound.setEnabled(True)
        # View Actions Set
        self.actionZoomInX.setEnabled(True)
        self.actionZoomOutX.setEnabled(False)
        self.actionZoomInY.setEnabled(True)
        self.actionZoomOutY.setEnabled(False)
        # Play Actions Set
        self.actionPlay.setEnabled(True)
        self.actionPause.setEnabled(False)
        self.actionStop.setEnabled(False)
        self.actionPlaySpeedUp.setEnabled(True)
        self.actionPlaySpeedDown.setEnabled(True)
        self.actionPlaySpeedRollback.setEnabled(False)
        # Button Setting
        # PlayButtons Set
        self.playButton.setEnabled(True)
        self.pauseButton.setEnabled(False)
        self.stopButton.setEnabled(False)

    def spec_color_set_fuc(self, color_name):
        s = None
        if color_name == "inferno":
            self.actionInferno.setEnabled(False)
            self.actionBinary.setEnabled(True)
            self.actionCET.setEnabled(True)
        elif color_name == "binary_r":
            s = "matplotlib"
            self.actionInferno.setEnabled(True)
            self.actionBinary.setEnabled(False)
            self.actionCET.setEnabled(True)
        else:
            self.actionInferno.setEnabled(True)
            self.actionBinary.setEnabled(True)
            self.actionCET.setEnabled(False)
        self.spec_color_name = color_name
        cm = pg.colormap.get(color_name, source=s).getLookupTable()
        self.spec_widget.img.setLookupTable(cm)

    def mk_play_line_set_fuc(self):
        self.wave_widget.lines.sigPositionChanged.connect(self.wave_line_synchro_fuc)
        self.spec_widget.lines.sigPositionChanged.connect(self.spec_line_synchro_fuc)

    # RoI Function Part
    def mk_roi_to(self, to_, roi_id, point1, point2):
        start_point = self.wave_widget._plotViewBox.mapSceneToView(point2)
        start_x = round(start_point.x(), 3) - 0.001
        end_point = self.spec_widget._plotViewBox.mapSceneToView(point1)
        end_x = round(end_point.x(), 3) + 0.001
        if start_x > end_x:
            tmp = start_x
            start_x = end_x
            end_x = tmp
        self.state["roi_data"][roi_id] = {"index": 0, "pos_s_x": start_x, "pos_e_x": end_x}
        self.state["line_range"] = [start_x, end_x]
        self.player.setPosition(int((start_x + 0.001) * 1000))
        self.wave_widget.lines.setPos([start_x, 0])
        self.spec_widget.lines.setPos([start_x, 0])
        self.state["playtype"] = 1
        self.state["current_roi"] = roi_id

        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.stop()
            self.playButton.setEnabled(True)
            self.pauseButton.setEnabled(False)
            self.stopButton.setEnabled(False)
        if to_ == "tospec":
            self.state["current_roi_type"] = "w"
            self.spec_widget.mk_roi_sync_fuc(roi_id, point1, point2)
        else:
            self.state["current_roi_type"] = "s"
            self.wave_widget.mk_roi_sync_fuc(roi_id, point1, point2)

    def roi_size_fuc(self, to_, roi_num, pos_s_x, pos_e_x):
        if to_ == "tospec":
            self.spec_widget.roi_change_fuc(roi_num, pos_s_x, pos_e_x)
        elif to_ == "towave":
            self.wave_widget.roi_change_fuc(roi_num, pos_s_x, pos_e_x)

    def roi_remove_fuc(self, ctrl, name):
        if ctrl == "remove":
            del(self.state["roi_data"]["{}".format(name)])
            self.wave_widget.remove_roi_fuc(name)
            self.spec_widget.remove_roi_fuc(name)
            self.state["playtype"] = 0

    def roi_clicked_fuc(self, pos_s_x, pos_e_x):
        start_x = round(pos_s_x, 3) - 0.001
        end_x = round(pos_e_x, 3) + 0.001
        self.state["line_range"] = [start_x, end_x]
        self.player.setPosition(int(pos_s_x * 1000))
        self.wave_widget.lines.setPos([start_x, 0])
        self.spec_widget.lines.setPos([start_x, 0])
        self.state["playtype"] = 1

    # UI Function Part
    def scrollbar_synchro_fuc(self, value):
        self.scrollArea_2.horizontalScrollBar().setSliderPosition(value)

    def scrollbar_2_synchro_fuc(self, value):
        self.scrollArea.horizontalScrollBar().setSliderPosition(value)

    def zoom_screen_fuc(self):
        self.wave_widget.x_length = 150 + (self.x_zoom_int * 120)
        self.spec_widget.x_length = 150 + (self.x_zoom_int * 120)
        self.spec_widget.y_length = 180 + (self.y_zoom_int * 50)
        self.wave_widget.size_refresh()
        self.spec_widget.size_refresh()
        self.scrollArea_2.setMaximumHeight(self.spec_widget.y_length + 10)
        self.scrollArea_2.setMinimumHeight(self.spec_widget.y_length + 10)
        self.zoom_x_action_fuc()
        self.zoom_y_action_fuc()

    # View Function Part
    def zoom_in_x_fuc(self):
        if self.current_file_name != "":
            if 0 <= self.x_zoom_int < 10:
                self.x_zoom_int += 1
                self.zoom_screen_fuc()

    def zoom_out_x_fuc(self):
        if self.current_file_name != "":
            if 0 < self.x_zoom_int <= 10:
                self.x_zoom_int -= 1
                self.zoom_screen_fuc()

    def zoom_x_action_fuc(self):
        if self.x_zoom_int >= 10:
            self.actionZoomInX.setEnabled(False)
            self.actionZoomOutX.setEnabled(True)
        elif self.x_zoom_int <= 0:
            self.actionZoomOutX.setEnabled(False)
            self.actionZoomInX.setEnabled(True)
        else:
            self.actionZoomInX.setEnabled(True)
            self.actionZoomOutX.setEnabled(True)
        self.zoom_rollback_action_fuc()
        self.zoom_button_fuc()

    def zoom_in_y_fuc(self):
        if self.current_file_name != "":
            if 0 <= self.y_zoom_int < 5:
                self.y_zoom_int += 1
                self.zoom_screen_fuc()
                maximum_int = self.scrollArea_2.verticalScrollBar().maximum()
                self.scrollArea_2.verticalScrollBar().setSliderPosition(maximum_int)

    def zoom_out_y_fuc(self):
        if self.current_file_name != "":
            if 0 < self.y_zoom_int <= 5:
                self.y_zoom_int -= 1
                self.zoom_screen_fuc()
                maximum_int = self.scrollArea_2.verticalScrollBar().maximum()
                self.scrollArea_2.verticalScrollBar().setSliderPosition(maximum_int)

    def zoom_y_action_fuc(self):
        if self.y_zoom_int >= 5:
            self.actionZoomInY.setEnabled(False)
            self.actionZoomOutY.setEnabled(True)
        elif self.y_zoom_int <= 0:
            self.actionZoomOutY.setEnabled(False)
            self.actionZoomInY.setEnabled(True)
        else:
            self.actionZoomInY.setEnabled(True)
            self.actionZoomOutY.setEnabled(True)
        self.zoom_rollback_action_fuc()
        self.zoom_button_fuc()

    def zoom_rollback_action_fuc(self):
        if self.x_zoom_int == 0 and self.y_zoom_int == 0:
            self.actionZoomRollback.setEnabled(False)
        else:
            self.actionZoomRollback.setEnabled(True)
    
    def zoom_button_fuc(self):
        self.zoomInXButton.setEnabled(self.actionZoomInX.isEnabled())
        self.zoomOutXButton.setEnabled(self.actionZoomOutX.isEnabled())
        self.zoomInYButton.setEnabled(self.actionZoomInY.isEnabled())
        self.zoomOutYButton.setEnabled(self.actionZoomOutY.isEnabled())
        self.zoomRollbackButton.setEnabled(self.actionZoomRollback.isEnabled())

    def zoom_rollback_fuc(self):
        self.x_zoom_int = 0
        self.y_zoom_int = 0
        self.wave_widget.x_length = 150
        self.wave_widget.y_length = 180
        self.wave_widget.size_refresh()
        self.spec_widget.x_length = 150
        self.spec_widget.y_length = 180
        self.spec_widget.size_refresh()
        self.scrollArea_2.setMaximumHeight(self.spec_widget.y_length + 10)
        self.scrollArea_2.setMinimumHeight(self.spec_widget.y_length + 10)
        self.zoom_x_action_fuc()
        self.zoom_y_action_fuc()

    def wave_widget_hide_and_show_fuc(self, checked):
        if checked:
            self.scrollArea.show()
        else:
            self.scrollArea.hide()

    def spec_widget_hide_and_show_fuc(self, checked):
        if checked:
            self.scrollArea_2.show()
        else:
            self.scrollArea_2.hide()

    # Player Function Part
    def set_to_player(self, local_path):
        url = QUrl.fromLocalFile(local_path)
        self.player.setMedia(QMediaContent(url))

    def play_sound_fuc(self):
        self.player.play()
        self.playButton.setEnabled(False)
        self.pauseButton.setEnabled(True)
        self.stopButton.setEnabled(True)

    def pause_sound_fuc(self):
        self.player.pause()
        self.playButton.setEnabled(True)
        self.pauseButton.setEnabled(False)

    def stop_sound_fuc(self):
        if self.state["playtype"] == 0:
            self.player.stop()
            self.playButton.setEnabled(True)
            self.pauseButton.setEnabled(False)
            self.stopButton.setEnabled(False)
            self.wave_widget.lines.setPos([0, 0])
            self.spec_widget.lines.setPos([0, 0])
        elif self.state["playtype"] == 1:
            self.player.stop()
            self.playButton.setEnabled(True)
            self.pauseButton.setEnabled(False)
            self.stopButton.setEnabled(False)
            self.player.setPosition(int(self.state["line_range"][0] * 1000)+2)
            self.wave_widget.lines.setPos([self.state["line_range"][0], 0])
            self.spec_widget.lines.setPos([self.state["line_range"][0], 0])

    def play_speed_up_fuc(self):
        if 1.0 <= self.play_speed_float < 4.0:
            self.play_speed_float = round(self.play_speed_float + 0.3, 2)
            self.player.setPlaybackRate(self.play_speed_float)
            self.play_speed_button_fuc()
        else:
            self.play_speed_float = round(self.play_speed_float + 0.05, 2)
            self.player.setPlaybackRate(self.play_speed_float)
            self.play_speed_button_fuc()

    def play_speed_down_fuc(self):
        if 1.0 < self.play_speed_float <= 4.0:
            self.play_speed_float = round(self.play_speed_float - 0.3, 2)
            self.player.setPlaybackRate(self.play_speed_float)
            self.play_speed_button_fuc()
        else:
            self.play_speed_float = round(self.play_speed_float - 0.05, 2)
            self.player.setPlaybackRate(self.play_speed_float)
            self.play_speed_button_fuc()

    def play_speed_rollback_fuc(self):
        self.play_speed_float = 1.0
        self.player.setPlaybackRate(self.play_speed_float)
        self.play_speed_button_fuc()

    def play_speed_button_fuc(self):
        if self.play_speed_float == 1.0:
            self.actionPlaySpeedUp.setEnabled(True)
            self.actionPlaySpeedDown.setEnabled(True)
            self.actionPlaySpeedRollback.setEnabled(False)
        elif self.play_speed_float == 4.0:
            self.actionPlaySpeedUp.setEnabled(False)
            self.actionPlaySpeedDown.setEnabled(True)
            self.actionPlaySpeedRollback.setEnabled(True)
        elif self.play_speed_float == 0.25:
            self.actionPlaySpeedUp.setEnabled(True)
            self.actionPlaySpeedDown.setEnabled(False)
            self.actionPlaySpeedRollback.setEnabled(True)
        else:
            self.actionPlaySpeedUp.setEnabled(True)
            self.actionPlaySpeedDown.setEnabled(True)
            self.actionPlaySpeedRollback.setEnabled(True)

    def wave_line_synchro_fuc(self):
        if self.player.state() != QMediaPlayer.PlayingState:
            self.spec_widget.lines.setPos(self.wave_widget.lines.pos())

    def spec_line_synchro_fuc(self):
        if self.player.state() != QMediaPlayer.PlayingState:
            self.wave_widget.lines.setPos(self.spec_widget.lines.pos())

    # Edit Functions Part
    def add_sound_main_fuc(self):
        filter_ = "(*.wav)"
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, '파일 선택', filter=filter_)[0]
        new_sound_data, new_sr = sf.read(file_path)
        if self.add_sound_part_1_fuc() == QtWidgets.QMessageBox.No:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Information)
            msgbox.setWindowTitle("Cancel")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setText("더하기 작업이 취소됐습니다.")
            msgbox.exec_()
            return
        if self.add_sound_part_2_fuc(new_sr) == QtWidgets.QMessageBox.No:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Information)
            msgbox.setWindowTitle("Cancel")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setText("더하기 작업이 취소됐습니다.")
            msgbox.exec_()
            return
        if new_sound_data.ndim == 2:
            new_sound_data = new_sound_data.mean(axis=1)
        x_index = int(self.wave_widget.lines.pos().x() * self.current_sound_sr)
        self.current_sound_data = np.concatenate([self.current_sound_data[:x_index], new_sound_data,
                                                  self.current_sound_data[x_index:]])
        before_scroll_value = self.scrollArea.horizontalScrollBar().value()
        self.setting_time_fuc()
        self.draw_wavefrom_plot_fuc()
        self.draw_spectrogram_plot_fuc()
        self.plotting_init(self.x_zoom_int, self.y_zoom_int)
        self.common_sound_part_fuc()
        self.scrollArea.horizontalScrollBar().setValue(before_scroll_value)

        msgbox = QtWidgets.QMessageBox()
        msgbox.setIcon(QtWidgets.QMessageBox.Information)
        msgbox.setWindowTitle("Done!")
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgbox.setText("더하기 작업이 완료되었습니다!")
        msgbox.exec_()

    def add_sound_part_1_fuc(self):
        if self.state["roi_data"]:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Information)
            msgbox.setWindowTitle("Boxing Warning")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.No)
            msgbox.setText("소리 데이터 수정시 모든 BoxData가 제거됩니다. \n 그래도 진행하시겠습니까?")
            ret = msgbox.exec_()
            return ret

    def add_sound_part_2_fuc(self, input_sr):
        if not (self.current_sound_sr == input_sr):
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Information)
            msgbox.setWindowTitle("SampleRate Warning")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.No)
            msgbox.setText("SampleRate가 서로 다릅니다. 이 경우 처리에 시간이 오래걸릴 수도 있습니다.\n그래도 진행하시겠습니까?")
            ret = msgbox.exec_()
            return ret

    def common_sound_part_fuc(self):
        key_tuple = list(self.state["roi_data"].keys())
        for key_ in key_tuple:
            del (self.state["roi_data"]["{}".format(key_)])
            self.state["playtype"] = 0

    def cut_sound_main_fuc(self):
        if self.cut_sound_part_1_fuc() == QtWidgets.QMessageBox.No:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Information)
            msgbox.setWindowTitle("Cancel")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setText("자르기 작업이 취소됐습니다.")
            msgbox.exec_()
            return
        if self.state["current_roi_type"] == "l":
            if self.cut_sound_part_2_fuc() == QtWidgets.QMessageBox.No:
                msgbox = QtWidgets.QMessageBox()
                msgbox.setIcon(QtWidgets.QMessageBox.Information)
                msgbox.setWindowTitle("Cancel")
                msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msgbox.setText("자르기 작업이 취소됐습니다.")
                msgbox.exec_()
                return
            index_ = int(self.wave_widget.lines.pos().x() * self.current_sound_sr)
            self.current_sound_data = self.current_sound_data[:index_]
            before_scroll_value = self.scrollArea.horizontalScrollBar().value()
            self.setting_time_fuc()
            self.draw_wavefrom_plot_fuc()
            self.draw_spectrogram_plot_fuc()
            self.plotting_init(self.x_zoom_int, self.y_zoom_int)
        elif self.state["current_roi_type"] == "w" or self.state["current_roi_type"] == "s":
            point_ = self.wave_widget.return_pos(self.state["current_roi"])
            point_index = [int(point_[0] * self.current_sound_sr), int(point_[1] * self.current_sound_sr)]
            self.current_sound_data = np.concatenate([self.current_sound_data[:point_index[0]],
                                                      self.current_sound_data[point_index[1]:]])
            before_scroll_value = self.scrollArea.horizontalScrollBar().value()
            self.setting_time_fuc()
            self.draw_wavefrom_plot_fuc()
            self.draw_spectrogram_plot_fuc()
            self.plotting_init(self.x_zoom_int, self.y_zoom_int)
        else:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Information)
            msgbox.setWindowTitle("Error")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setText("자르기 작업이 취소됐습니다.")
            msgbox.exec_()
            return

        self.common_sound_part_fuc()
        self.scrollArea.horizontalScrollBar().setValue(before_scroll_value)

        msgbox = QtWidgets.QMessageBox()
        msgbox.setIcon(QtWidgets.QMessageBox.Information)
        msgbox.setWindowTitle("Done!")
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgbox.setText("자르기 작업이 완료되었습니다!")
        msgbox.exec_()

    def cut_sound_part_1_fuc(self):
        if len(self.state["roi_data"]) > 1:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Information)
            msgbox.setWindowTitle("Boxing Warning")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.No)
            msgbox.setText("소리 데이터 수정시 모든 BoxData가 제거됩니다. \n그래도 진행하시겠습니까?")
            ret = msgbox.exec_()
            return ret

    def cut_sound_part_2_fuc(self):
        msgbox = QtWidgets.QMessageBox()
        msgbox.setIcon(QtWidgets.QMessageBox.Information)
        msgbox.setWindowTitle("Range Warning")
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.No)
        msgbox.setText("선택 범위 이후의 모든 데이터가 삭제됩니다. \n그래도 진행하시겠습니까?")
        ret = msgbox.exec_()
        return ret
    
    def silence_sound_main_fuc(self):
        if self.cut_sound_part_1_fuc() == QtWidgets.QMessageBox.No:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Information)
            msgbox.setWindowTitle("Cancel")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setText("음소거 작업이 취소됐습니다.")
            msgbox.exec_()
            return
        if self.state["current_roi_type"] == "l":
            if self.silence_sound_part_2_fuc() == QtWidgets.QMessageBox.No:
                msgbox = QtWidgets.QMessageBox()
                msgbox.setIcon(QtWidgets.QMessageBox.Information)
                msgbox.setWindowTitle("Cancel")
                msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msgbox.setText("음소거 작업이 취소됐습니다.")
                msgbox.exec_()
                return
            index_ = int(self.wave_widget.lines.pos().x() * self.current_sound_sr)
            silence_np = self.current_sound_data[index_:]
            np.putmask(silence_np, silence_np != 0, 0)
            self.current_sound_data = np.concatenate([self.current_sound_data[:index_], silence_np])
            before_scroll_value = self.scrollArea.horizontalScrollBar().value()
            self.setting_time_fuc()
            self.draw_wavefrom_plot_fuc()
            self.draw_spectrogram_plot_fuc()
            self.plotting_init(self.x_zoom_int, self.y_zoom_int)
        elif self.state["current_roi_type"] == "w" or self.state["current_roi_type"] == "s":
            point_ = self.wave_widget.return_pos(self.state["current_roi"])
            point_index = [int(point_[0] * self.current_sound_sr), int(point_[1] * self.current_sound_sr)]
            silence_np = self.current_sound_data[point_index[0]:point_index[1]]
            np.putmask(silence_np, silence_np != 0, 0)
            self.current_sound_data = np.concatenate([self.current_sound_data[:point_index[0]], silence_np,
                                                      self.current_sound_data[point_index[1]:]])
            before_scroll_value = self.scrollArea.horizontalScrollBar().value()
            self.setting_time_fuc()
            self.draw_wavefrom_plot_fuc()
            self.draw_spectrogram_plot_fuc()
            self.plotting_init(self.x_zoom_int, self.y_zoom_int)
        else:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Information)
            msgbox.setWindowTitle("Error")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setText("자르기 작업이 취소됐습니다.")
            msgbox.exec_()
            return

        self.common_sound_part_fuc()
        self.scrollArea.horizontalScrollBar().setValue(before_scroll_value)
        msgbox = QtWidgets.QMessageBox()
        msgbox.setIcon(QtWidgets.QMessageBox.Information)
        msgbox.setWindowTitle("Done!")
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgbox.setText("음소거 작업이 완료되었습니다!")
        msgbox.exec_()
        
    def silence_sound_part_1_fuc(self):
        if len(self.state["roi_data"]) > 1:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Information)
            msgbox.setWindowTitle("Boxing Warning")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.No)
            msgbox.setText("소리 데이터 수정시 모든 BoxData가 제거됩니다. \n그래도 진행하시겠습니까?")
            ret = msgbox.exec_()
            return ret

    def silence_sound_part_2_fuc(self):
        msgbox = QtWidgets.QMessageBox()
        msgbox.setIcon(QtWidgets.QMessageBox.Information)
        msgbox.setWindowTitle("Range Warning")
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.No)
        msgbox.setText("선택 범위 이후의 모든 소리가 없어집니다. \n그래도 진행하시겠습니까?")
        ret = msgbox.exec_()
        return ret
    
    def cut_spectrogram_main_fuc(self):
        if self.state["current_roi_type"] != "s":
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)
            msgbox.setWindowTitle("Selection Error")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setText("잘라낼 Spectrogram 영역을 만들거나 선택해 주세요.")
            msgbox.exec_()
            return
        if self.cut_spectrogram_part_1_fuc() == QtWidgets.QMessageBox.No:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Information)
            msgbox.setWindowTitle("Cancel")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setText("자르기 작업이 취소됐습니다.")
            msgbox.exec_()
            return
        point_, size_ = self.spec_widget.return_pos(self.state["current_roi"])
        endPoint_ = point_ + size_
        minX, maxX, minY, maxY = int(point_.x() * self.current_sound_sr), int(endPoint_.x() * self.current_sound_sr),\
                                 point_.y(), endPoint_.y()
        if minX > maxX:
            tmp = minX
            minX = maxX
            maxX = tmp
        if minY > maxY:
            tmp = minY
            minY = maxY
            maxY = tmp
        filter_data = self.cut_spectrogram_filter_fuc(self.current_sound_data[minX:maxX], minY, maxY,
                                                      self.current_sound_sr, order=4)
        self.current_sound_data = np.concatenate([self.current_sound_data[:minX], filter_data,
                                                  self.current_sound_data[maxX:]])
        before_scroll_value = self.scrollArea.horizontalScrollBar().value()
        self.setting_time_fuc()
        self.draw_wavefrom_plot_fuc()
        self.draw_spectrogram_plot_fuc()
        self.plotting_init(self.x_zoom_int, self.y_zoom_int)
        self.common_sound_part_fuc()
        self.scrollArea.horizontalScrollBar().setValue(before_scroll_value)

        msgbox = QtWidgets.QMessageBox()
        msgbox.setIcon(QtWidgets.QMessageBox.Information)
        msgbox.setWindowTitle("Done!")
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgbox.setText("자르기 작업이 완료되었습니다!")
        msgbox.exec_()

    def cut_spectrogram_part_1_fuc(self):
        if len(self.state["roi_data"]) > 1:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Information)
            msgbox.setWindowTitle("Boxing Warning")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.No)
            msgbox.setText("소리 데이터 수정시 모든 BoxData가 제거됩니다. \n그래도 진행하시겠습니까?")
            ret = msgbox.exec_()
            return ret

    def cut_spectrogram_filter_fuc(self, data, lowcut, higcut, fs, order=5):
        if lowcut < 10:
            lowcut = 10
        if higcut > fs - 7:
            higcut = fs - 7
        nyp = fs * 0.5
        low = lowcut / nyp
        high = higcut / nyp
        b, a = butter(order, [low, high], btype='bandstop')
        sound_data = filtfilt(b, a, data)
        return sound_data

    # Tools Functions Part
    def file_concat_dialog_fuc(self):
        sub_concat_dialog = ConcatDialog()
        sub_concat_dialog.exec_()

    def file_divide_dialog_fuc(self):
        sub_concat_dialog = DivideDialog()
        sub_concat_dialog.exec_()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    sys.exit(app.exec_())
