import getpass
import glob
import random
import sys
import os

import numpy as np
import librosa
import soundfile as sf
import wave
from PyQt5 import QtWidgets, uic


class ConcatDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        _ui = "./UI/concat_dialog.ui"
        uic.loadUi(_ui, self)

        self.user_name = getpass.getuser()
        self.save_folder_name = "C:/Users/{}/Documents/SoundEditor/".format(self.user_name)
        self.current_file_names = []
        self.current_folder_name = ""
        self.total_time = 0
        self.file_counting = 1
        self.preview_text = "1"
        self.mk_counting = False
        self.remove_role = False
        self.shuffle_role = False

        self.loading_fuc()

    def loading_fuc(self):
        self.ui_init()
        self.button_init()
        self.function_init()
        self.setting_init()

    def button_init(self):
        self.findButton.clicked.connect(self.save_folder_find_fuc)
        self.loadFileButton.clicked.connect(self.load_file_fuc)
        self.loadFolderButton.clicked.connect(self.load_folder_fuc)
        self.doButton.clicked.connect(self.do_concatenate)
        self.closeButton.clicked.connect(self.close)

    def function_init(self):
        self.fileCountCheckBox.stateChanged.connect(self.file_count_setting)
        self.removeRoleCheckBox.stateChanged.connect(self.remove_role_setting)
        self.shuffleCheckBox.stateChanged.connect(self.shuffle_role_setting)
        self.countingTextBrowser.textChanged.connect(self.counting_file_check)
        self.saveTextBrowser.textChanged.connect(self.save_locate_change)

    def ui_init(self):
        _qr = self.frameGeometry()
        _cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        _qr.moveCenter(_cp)
        self.fileLoadTableWidget.setColumnWidth(0, int(300 * 0.6))
        self.fileLoadTableWidget.setColumnWidth(1, int(300 * 0.25))

    def setting_init(self):
        self.setAcceptDrops(True)
        if not os.path.exists(self.save_folder_name):
            os.mkdir(self.save_folder_name)

    # Mouse Functions
    def dragEnterEvent(self, e):
        for url in e.mimeData().urls():
            if not (url.isEmpty()) or ".wav" in url.toLocalFile():
                e.accept()
            else:
                e.ignore()

    def dropEvent(self, e):
        self.current_file_names = []
        for url in e.mimeData().urls():
            if ".wav" in url.toLocalFile() or not (url.isEmpty()):
                e.accept()
                if url.toLocalFile()[-4:] == ".wav":
                    self.current_file_names.append(url.toLocalFile())
                else:
                    tmp_file_names = glob.glob(url.toLocalFile() + "/*.wav")
                    self.current_file_names.extend(tmp_file_names)
            else:
                e.ignore()
        self.load_to_table_widget_fuc(self.current_file_names)

    # Load Functions
    def save_folder_find_fuc(self):
        self.save_folder_name = QtWidgets.QFileDialog.getExistingDirectory(self, '저장 위치 선택')
        self.saveTextBrowser.setText(self.save_folder_name)

    def load_file_fuc(self):
        filter_ = "*.wav"
        self.current_file_names, _ = QtWidgets.QFileDialog.getOpenFileNames(self, '대상 파일들 선택', filter=filter_)
        self.load_to_table_widget_fuc(self.current_file_names)

    def load_folder_fuc(self):
        self.current_folder_name = QtWidgets.QFileDialog.getExistingDirectory(self, "대상 폴더 선택")
        self.current_file_names = glob.glob(self.current_folder_name + "/*.wav")
        self.load_to_table_widget_fuc(self.current_file_names)

    def load_to_table_widget_fuc(self, file_list):
        self.fileLoadTableWidget.setRowCount(len(file_list))
        if not file_list:
            self.fileCountCheckBox.setEnabled(False)
            self.removeRoleCheckBox.setEnabled(False)
            self.shuffleCheckBox.setEnabled(False)
            self.doButton.setEnabled(False)
        else:
            for i in range(len(file_list)):
                file_path = file_list[i].replace("\\", "/")
                audio = wave.open(file_path)
                frames = audio.getnframes()
                rate = audio.getframerate()
                duration = round(frames / rate, 3)
                file_name = file_path.split("/")[-1]
                self.fileLoadTableWidget.setItem(i, 0, QtWidgets.QTableWidgetItem(file_name))
                self.fileLoadTableWidget.setItem(i, 1, QtWidgets.QTableWidgetItem(str(duration)))
            self.fileCountCheckBox.setEnabled(True)
            self.removeRoleCheckBox.setEnabled(True)
            self.shuffleCheckBox.setEnabled(True)
            self.check_row_and_text()

    # Concatenate Expectancy Functions
    def calculate_expectancy(self):
        self.total_time = 0
        for i in range(self.fileLoadTableWidget.rowCount()):
            time_item = self.fileLoadTableWidget.item(i, 1).text()
            self.total_time += float(time_item)
        self.file_counting = int(self.countingTextBrowser.toPlainText())

    def show_result(self, bools):
        if bools:
            n_times = round(self.total_time / self.file_counting, 3)
            self.msgLabel_1.setText(str(self.file_counting))
            self.msgLabel_2.setText(str(n_times))
            self.msgLabel_3.setText("Concatenate_Wave_****.wav")
            self.mk_counting = True
        else:
            self.msgLabel_1.setText("0")
            self.msgLabel_2.setText("0")
            self.msgLabel_3.setText("---")
            self.mk_counting = False

    # Concatenate Setting Functions
    def file_count_setting(self, check_bool):
        if check_bool:
            self.countingTextBrowser.setEnabled(True)
            self.countingTextBrowser.setText("1")
            self.mk_counting = True
        else:
            self.countingTextBrowser.setEnabled(False)
            self.countingTextBrowser.setText("1")
            self.mk_counting = False

    def remove_role_setting(self, check_bool):
        if check_bool:
            self.remove_role = True
        else:
            self.remove_role = False

    def shuffle_role_setting(self, check_bool):
        if check_bool:
            self.shuffle_role = True
        else:
            self.shuffle_role = False

    # Concatenate Functions
    def do_concatenate(self):
        self.check_before_concat()
        try:
            if self.mk_counting:
                con_sound_list = []
                con_sr_list = []
                con_ch_list = []
                con_sr = 0
                con_ch = 3
                progress_value = 10
                up_value = 1 / len(self.current_file_names) * 20
                for file_path in self.current_file_names:
                    file_path = file_path.replace("\\", "/")
                    tmp_sound, sr = sf.read(file_path)
                    ch = tmp_sound.ndim
                    con_sr_list.append(sr)
                    con_ch_list.append(ch)
                    progress_value += up_value
                    self.progressBar.setValue(int(progress_value))
                if not self.check_sr(con_sr_list):
                    con_sr = min(con_sr_list)
                if not self.check_ch(con_ch_list):
                    con_ch = self.check_ch(con_ch_list)
                progress_value = 30

                up_value = 1 / len(self.current_file_names) * 40
                for file_path in self.current_file_names:
                    file_path = file_path.replace("\\", "/")
                    sound, sr = librosa.load(file_path, sr=con_sr, mono=con_ch)
                    if sound.ndim != 1 and con_ch:
                        sound = sound.mean(axis=1)
                    con_sound_list.append(sound)
                    progress_value += up_value
                    self.progressBar.setValue(int(progress_value))
                k = 1
                if con_ch:
                    k = 0
                all_sound_np = np.concatenate(con_sound_list, axis=k)
                progress_value = 70

                division = all_sound_np.shape[1] // self.file_counting
                to_file_sound = []
                up_value = 1 / self.file_counting * 15
                for i in range(self.file_counting):
                    if all_sound_np.shape[1] >= division and con_ch:
                        all_sound_np_tmp = all_sound_np[:division]
                        all_sound_np = all_sound_np[division:]
                    elif all_sound_np.shape[1] < division and con_ch:
                        all_sound_np_tmp = all_sound_np[:]
                    elif all_sound_np.shape[1] >= division and not con_ch:
                        all_sound_np_tmp = all_sound_np[:, :division]
                        all_sound_np = all_sound_np[:, division:]
                    else:
                        all_sound_np_tmp = all_sound_np[:, :]
                    to_file_sound.append(all_sound_np_tmp)
                    progress_value += up_value
                    self.progressBar.setValue(int(progress_value))
                progress_value = 85

                n = 1
                up_value = 1 / len(to_file_sound) * 15
                for sound_data in to_file_sound:
                    file_name = self.msgLabel_3.text().replace("****", "{:04d}")
                    path_ = os.path.join(self.save_folder_name, file_name)
                    if sound_data.shape[0] == 2:
                        sound_data = sound_data.T
                    sf.write(path_.format(n), sound_data, samplerate=con_sr)
                    n += 1
                    progress_value += up_value
                    self.progressBar.setValue(int(progress_value))

            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Information)
            msgbox.setWindowTitle("합치기 완료")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setText("합치기가 완료되었습니다!")
            msgbox.exec_()
            self.progressBar.setValue(0)
            self.do_option()

        except:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)
            msgbox.setWindowTitle("합치기 실패...")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setText("합치기 중 오류가 발생하여 합치기를 실패했습니다.")
            msgbox.exec_()
            self.progressBar.setValue(0)

    def check_before_concat(self):
        if not os.path.exists(self.saveTextBrowser.toPlainText()):
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)
            msgbox.setWindowTitle("경로 탐색 실패")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setText("저장 경로가 존재하지 않습니다.")
            msgbox.exec_()
            self.mk_counting = False
            return
        if len(self.current_file_names) <= 1:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)
            msgbox.setWindowTitle("대상 부족 실패")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setText("합칠 대상이 2개 이상이여야 합니다.")
            msgbox.exec_()
            self.mk_counting = False
            return
        if len(self.current_file_names) < self.file_counting:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)
            msgbox.setWindowTitle("결과 부적합")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setText("최종 결과의 수는 합칠 대상보다 적어야합니다.")
            msgbox.exec_()
            self.mk_counting = False
            return
        if self.shuffle_role:
            random.shuffle(self.current_file_names)
        self.progressBar.setValue(10)
        self.mk_counting = True

    def check_sr(self, sr_list):
        if len(sr_list) == 1:
            return True
        if max(sr_list) != min(sr_list):
            return False
        else:
            return True

    def check_ch(self, ch_list):
        if len(ch_list) == 1:
            return True
        if 2 == min(ch_list):
            return False
        else:
            return True

    def do_option(self):
        if self.remove_role:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Information)
            msgbox.setWindowTitle("원본 삭제")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.No)
            msgbox.setText("정말 원본을 삭제하겠습니까?")
            ret = msgbox.exec_()
            if ret == QtWidgets.QMessageBox.Ok:
                for file_path in self.current_file_names:
                    os.remove(file_path)
                self.fileLoadTableWidget.clearContents()

    # Input UI Setting Functions
    def counting_file_check(self):
        counting_num = self.countingTextBrowser.toPlainText()
        if len(counting_num) == 0:
            self.preview_text = counting_num
            self.msgLabel_4.setText("실행 불가")
            self.doButton.setEnabled(False)
        else:
            for char_ in counting_num:
                if not (48 <= ord(char_) <= 57):
                    msgbox = QtWidgets.QMessageBox()
                    msgbox.setIcon(QtWidgets.QMessageBox.Warning)
                    msgbox.setWindowTitle("정수 입력 실패")
                    msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
                    msgbox.setText("숫자만 입력해주십시오!")
                    msgbox.exec_()
                    self.countingTextBrowser.setText(self.preview_text)
                    return
            self.preview_text = counting_num
            self.check_row_and_text()

    def check_row_and_text(self):
        if int(self.preview_text) == 0:
            self.show_result(False)
            self.msgLabel_4.setText("실행 불가")
            self.doButton.setEnabled(False)
        elif self.fileLoadTableWidget.rowCount() > int(self.preview_text):
            self.calculate_expectancy()
            self.show_result(True)
            self.msgLabel_4.setText("실행 가능")
            self.doButton.setEnabled(True)
        else:
            self.show_result(False)
            self.msgLabel_4.setText("실행 불가")
            self.doButton.setEnabled(False)

    def save_locate_change(self):
        self.save_folder_name = self.saveTextBrowser.toPlainText()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main = ConcatDialog()
    main.show()
    sys.exit(app.exec_())
