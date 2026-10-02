import os
import sys
import traceback

from PyQt5.QtCore import QStandardPaths, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QGridLayout, QLabel,
    QMessageBox, QProgressBar, QPushButton, QSpinBox, QWidget,
)

import func_conv


# ----------------------------------------------------------------------------
# Поток конвертации
# ----------------------------------------------------------------------------

class ConvertThread(QThread):
    """Выполняет конвертацию, не блокируя GUI."""

    succeeded = pyqtSignal(str)   # путь к созданному файлу
    failed = pyqtSignal(str)      # текст ошибки

    def __init__(self, path, option, duration, parent=None):
        super().__init__(parent)
        self._path = path
        self._option = option
        self._duration = duration

    def run(self):
        try:
            result_path = self._dispatch()
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.succeeded.emit(result_path)

    def _dispatch(self) -> str:
        option = self._option
        path = self._path
        duration = self._duration

        handlers = {
            'Stand':        lambda: func_conv.stand(path, duration),
            'TV':           lambda: func_conv.tv(path),
            'BC':           lambda: func_conv.bc(path, duration),
            'Stand(Video)': lambda: func_conv.stand_video(path),
            'BC(video)':    lambda: func_conv.bc_video(path),
            'TV_Picture':   lambda: func_conv.tv_from_picture(path, duration),
        }
        handler = handlers.get(option)
        if handler is None:
            raise ValueError(f'Неизвестный режим: {option}')
        return handler()


# ----------------------------------------------------------------------------
# Окно
# ----------------------------------------------------------------------------

class ConverterWindow(QWidget):

    OPTIONS = ["Stand", "TV", "BC", "Stand(Video)", "BC(video)", "TV_Picture"]
    VIDEO_OPTIONS = {'TV', 'Stand(Video)', 'BC(video)'}   # где на входе видео
    DURATION_OPTIONS = {'Stand', 'BC', 'TV_Picture'}      # где нужна длительность

    def __init__(self):
        super().__init__()
        self._init_state()
        self._create_widgets()
        self._create_layout()
        self._connect_signals()
        self._update_duration_visibility()
        self.setWindowTitle('Converter')

    # ---------- инициализация ----------

    def _init_state(self):
        self._path = None
        self._convert_thread = None

    def _create_widgets(self):
        self.ledDuration = QLabel('Укажите длительность видео')
        self.duration = QSpinBox()
        self.duration.setRange(10, 180)
        self.duration.setValue(30)

        self.options = QComboBox()
        self.options.addItems(self.OPTIONS)

        self.ledText = QLabel('Файл не выбран')
        self.ledProgres = QLabel('Состояние')

        self.btnUpdate = QPushButton('Choose file')
        self.btnConvert = QPushButton('Convert')

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)

    def _create_layout(self):
        grid = QGridLayout(self)
        grid.setSpacing(20)
        grid.addWidget(self.ledText,     0, 0)
        grid.addWidget(self.btnUpdate,   1, 0)
        grid.addWidget(self.btnConvert,  2, 0)
        grid.addWidget(self.options,     3, 0)
        grid.addWidget(self.ledProgres,  4, 0)
        grid.addWidget(self.bar,         5, 0, 1, 3)
        grid.addWidget(self.ledDuration, 0, 1)
        grid.addWidget(self.duration,    1, 1)

    def _connect_signals(self):
        self.btnConvert.clicked.connect(self._on_convert_clicked)
        self.btnUpdate.clicked.connect(self._on_choose_clicked)
        self.options.currentTextChanged.connect(self._update_duration_visibility)

    # ---------- слоты ----------

    def _on_choose_clicked(self):
        if self.options.currentText() in self.VIDEO_OPTIONS:
            filter_str = 'Video (*.mp4 *.avi *.mov)'
            start_dir = self._default_dir(QStandardPaths.MoviesLocation)
        else:
            filter_str = 'Images (*.jpg *.jpeg *.png *.PNG)'
            start_dir = self._default_dir(QStandardPaths.DesktopLocation)

        path, _ = QFileDialog.getOpenFileName(
            self, 'Open File', directory=start_dir, filter=filter_str,
        )
        if not path:
            return  # пользователь отменил выбор

        self._path = path
        self.ledText.setText(os.path.basename(path))

    def _on_convert_clicked(self):
        if not self._path:
            self._show_message('Ошибка пути', 'Выберите файл', QMessageBox.Warning)
            self.ledText.setText('Файл не выбран')
            return

        option = self.options.currentText()
        duration = self.duration.value()

        self._set_busy(True)
        self.ledText.setText('Подождите, идёт конвертация...')
        self.bar.setRange(0, 0)  # бесконечный прогресс — Qt сам анимирует

        self._convert_thread = ConvertThread(self._path, option, duration, parent=self)
        self._convert_thread.succeeded.connect(self._on_convert_succeeded)
        self._convert_thread.failed.connect(self._on_convert_failed)
        self._convert_thread.finished.connect(self._on_thread_finished)
        self._convert_thread.start()

    def _on_convert_succeeded(self, result_path: str):
        self.bar.setRange(0, 100)
        self.bar.setValue(100)

        box = QMessageBox(self)
        box.setWindowTitle('Конвертация')
        box.setIcon(QMessageBox.Information)
        box.setText('Конвертация успешно завершена!')
        box.setInformativeText(f'Файл сохранён:\n{result_path}')
        box.exec_()

        self._reset_after_conversion()

    def _on_convert_failed(self, message: str):
        self.bar.setRange(0, 100)
        self.bar.setValue(0)

        box = QMessageBox(self)
        box.setWindowTitle('Ошибка конвертации')
        box.setIcon(QMessageBox.Warning)
        box.setText('Не удалось выполнить конвертацию.')
        box.setDetailedText(message)
        box.exec_()

        self._reset_after_conversion()

    def _on_thread_finished(self):
        self._convert_thread = None

    # ---------- вспомогательное ----------

    def _reset_after_conversion(self):
        self._set_busy(False)
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.ledText.setText('Файл не выбран')
        self._path = None

    def _set_busy(self, busy: bool):
        self.btnConvert.setEnabled(not busy)
        self.btnUpdate.setEnabled(not busy)
        self.options.setEnabled(not busy)
        self.duration.setEnabled(not busy and self._duration_needed())

    def _duration_needed(self) -> bool:
        return self.options.currentText() in self.DURATION_OPTIONS

    def _update_duration_visibility(self):
        needed = self._duration_needed()
        self.duration.setEnabled(needed)
        self.ledDuration.setEnabled(needed)

    def _show_message(self, title: str, text: str, icon):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setIcon(icon)
        box.setText(text)
        box.exec_()

    @staticmethod
    def _default_dir(kind) -> str:
        location = QStandardPaths.writableLocation(kind)
        return location or os.path.expanduser('~')

    # ---------- закрытие ----------

    def closeEvent(self, event):
        thread = self._convert_thread
        if thread is not None and thread.isRunning():
            answer = QMessageBox.question(
                self,
                'Конвертация',
                'Конвертация ещё идёт. Закрыть приложение?',
                QMessageBox.Yes | QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                event.ignore()
                return
            # Даём потоку шанс завершиться. Полноценная отмена ffmpeg
            # потребовала бы отдельного управления subprocess.
            thread.wait(3000)
        event.accept()


# ----------------------------------------------------------------------------
# Точка входа
# ----------------------------------------------------------------------------

def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("Обнаружена ошибка:", tb)


def main():
    sys.excepthook = excepthook
    app = QApplication(sys.argv)
    window = ConverterWindow()
    window.resize(500, 260)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()