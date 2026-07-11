import sys
import csv
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QShortcut
from PyQt5.QtGui import QFont, QPixmap, QImage, QKeySequence
from PyQt5.QtCore import QTimer, QSettings
from PIL import Image

from des import Ui_MainWindow
from database import DatabaseManager


logging.basicConfig(
    filename="program.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    encoding="utf-8"
)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self._setup_ui()

        self.ui.label_resulthistory.setMaximumHeight(150)
        
        self.settings = QSettings(
            "College",
            "TemperatureConverter"
        )

        geometry = self.settings.value("geometry")

        if geometry:
            self.restoreGeometry(geometry)

        self.setWindowTitle("Конвертер температур")

        self.db = DatabaseManager()
        self.db.init_db()

        self.timer = QTimer()
        self.timer.timeout.connect(self.clear_labels)

        self.bind_signals()
        QShortcut(QKeySequence("Ctrl+K"), self, self.add)
        QShortcut(QKeySequence("Ctrl+D"), self, self.delete)
        QShortcut(QKeySequence("Ctrl+E"), self, self.export_csv)

        self.load_image("thermometer.png")

        self.get_all()

        logging.info("Программа запущена")

    def _setup_ui(self):
        """Настройка интерфейса"""

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setStyleSheet("""
        QMainWindow {
            background-color: white;
        }

        QPushButton {
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
            padding: 5px;
        }

        QPushButton:hover {
            background-color: #45a049;
        }

        QLabel {
            font-size: 10pt;
        }

        QDoubleSpinBox {
            padding: 4px;
        }
        """)
        
    def bind_signals(self):
        """Подключение сигналов"""

        self.ui.pushButton_convert.clicked.connect(self.add)
        self.ui.pushButton_history.clicked.connect(self.delete)
        self.ui.pushButton_export.clicked.connect(self.export_csv)
        self.ui.pushButton_update.clicked.connect(self.update)

    def add(self):
        """Конвертация температуры"""
        
        c = self.ui.doubleSpinBox.value()

        f = c * 9 / 5 + 32
        k = c + 273.15

        logging.info(
            f"Конвертация: {c} °C -> {f:.2f} °F, {k:.2f} K"
        )

        self.ui.label_resultfahrenheit.setText(f"{f:.2f} °F")
        self.ui.label_resultkelvin.setText(f"{k:.2f} K")

        # заметки
        if c < 0:
            note = "Очень холодно"
        elif c < 10:
            note = "Холодно"
        elif c < 20:
            note = "Прохладно"
        elif c < 30:
            note = "Тепло"
        elif c < 40:
            note = "Жарко"
        else:
            note = "Очень жарко"

        self.ui.label_resultnotes.setText(note)

        # графическая шкала
        count = int((c + 50) / 15)

        if count < 0:
            count = 0

        if count > 10:
            count = 10

        scale = "■" * count + "□" * (10 - count)

        self.ui.label_picgrafscale.setText(scale)

        # запись в БД
        formula = "F = C × 9/5 + 32"

        image_path = "thermometer.png"

        try:
            self.db.add(
                c,
                f,
                k,
                formula,
                note,
                image_path
            )

            self.get_all()

            records = self.db.get_all()

            if len(records) >= 6:
                QMessageBox.warning(
                self,
                "История заполнена",
                "В истории много записей. Очистите историю."
            )

        except Exception as error:

            logging.error(
                f"Ошибка базы данных: {error}"
            )
                
            QMessageBox.critical(
                self,
                "Ошибка базы данных",
                str(error)
            )
            return
        
        self.timer.start(5000)
        
    def load_image(self, path):
        """Загрузка изображения через Pillow"""
        
        try:
            img = Image.open(path)
            img = img.convert("RGBA")
            img = img.resize((180, 280))

            qt_image = QImage(
                img.tobytes(),
                img.width,
                img.height,
                QImage.Format_RGBA8888
            )

            pixmap = QPixmap.fromImage(qt_image)

            self.ui.label_image.setPixmap(pixmap)

        except Exception as error:
            logging.error(
                f"Ошибка загрузки изображения: {error}"
            )
            self.ui.label_image.setText("Фото не найдено")

    def get_all(self):
        """Загрузка истории конвертаций из базы данных"""
        
        records = self.db.get_all()
            
        history = ""

        for row in records:
            history += (
                f"{row['temp_c']} °C → "
                f"{row['temp_f']} °F → "
                f"{row['temp_k']} K\n"
            )

        self.ui.label_resulthistory.setText(history)

    def update(self):
        """Изменение заметки"""
        
        current_note = self.ui.label_resultnotes.text()

        if current_note == "":
            QMessageBox.warning(
                self,
                "Ошибка",
                "Сначала выполните конвертацию"
            )
            return

        self.ui.label_resultnotes.setText("Изменено пользователем")

        QMessageBox.information(
            self,
            "Готово",
            "Заметка изменена"
        )
        
    def export_csv(self):
        """Экспорт истории температуры в CSV файл"""

        try:
            records = self.db.get_all()

            with open(
                "history.csv",
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "temp_c",
                    "temp_f",
                    "temp_k",
                    "formula",
                    "notes",
                    "image_path"
                ])

                for row in records:

                    writer.writerow([
                        row["temp_c"],
                        row["temp_f"],
                        row["temp_k"],
                        row["formula"],
                        row["notes"],
                        row["image_path"]
                    ])
            logging.info("История экспортирована в CSV")

            QMessageBox.information(
                self,
                "Готово",
                "CSV сохранён."
            )

        except Exception as error:
            logging.error(
                f"Ошибка экспорта CSV: {error}"
            )
            
            QMessageBox.critical(
                self,
                "Ошибка экспорта",
                str(error)
            )

    def delete(self):
        """Очистка истории"""

        reply = QMessageBox.question(
            self,
            "Очистка",
            "Очистить всю историю?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:

            self.db.delete()

            sender = self.sender()

            if sender:
                logging.info(
                    f"Очистка вызвана кнопкой: {sender.objectName()}"
                )
            else:
                logging.info(
                    f"Очистка вызвана программно"
                )
                
            self.ui.label_resulthistory.clear()

            QMessageBox.information(
                self,
                "Готово",
                "История очищена."
            )

    def clear_labels(self):
        """Очистка результатов"""

        self.ui.label_resultfahrenheit.clear()
        self.ui.label_resultkelvin.clear()
        self.ui.label_resultnotes.clear()
        self.ui.label_picgrafscale.clear()

        self.timer.stop()

    def closeEvent(self, event):
        """Обработка закрытия окна"""

        reply = QMessageBox.question(
            self,
            "Выход",
            "Закрыть программу?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            
            self.settings.setValue(
                "geometry",
                self.saveGeometry()
            )

            self.db.close()

            logging.info("Программа закрыта")
            event.accept()
        else:
            event.ignore()


def main():
    """Точка входа в программу"""

    try:
        app = QApplication(sys.argv)

        app.setApplicationName("TemperatureConverter")
        app.setApplicationVersion("1.0")

        app.setFont(QFont("Segoe UI", 10))

        window = MainWindow()
        window.show()

        sys.exit(app.exec_())

    except Exception as error:
        logging.error(
            f"Критическая ошибка приложения: {error}"

        )

if __name__ == "__main__":
    main()
