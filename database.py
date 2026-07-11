import sqlite3
import logging

class DatabaseManager:
    """Класс для работы с БД SQlite"""

    def __init__(self):
        """Создание объекта менеджера БД"""
        self.db_name = 'temperature.db'
        self.conn = None

    def init_db(self):
        """Создание БД и таблицы при первом запуске"""
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS temperatures(

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                temp_c REAL,

                temp_f REAL,

                temp_k REAL,

                formula TEXT,

                notes TEXT,

                image_path TEXT

            )
        """)

        self.conn.commit()

    def add(self, temp_c, temp_f, temp_k, formula, notes, image_path):
        """Добавление новой записи в БД"""
        cursor = self.conn.cursor()

        cursor.execute("""

            INSERT INTO temperatures
            (temp_c, temp_f, temp_k, formula, notes, image_path)

            VALUES (?, ?, ?, ?, ?, ?)

        """,
        (
            temp_c,
            temp_f,
            temp_k,
            formula,
            notes,
            image_path
        ))

        self.conn.commit()

    def update(self, id, temp_c):
        """Обновление температуры"""

        cursor = self.conn.cursor()

        cursor.execute("""
            UPDATE temperatures
            SET temp_c = ?
            WHERE id = ?
        """,
        (
            temp_c,
            id
        ))

        self.conn.commit()

    def get_all(self):
        """Получение всех записей из БД"""

        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT *
            FROM temperatures
            ORDER BY id ASC
        """)

        return cursor.fetchall()

    def delete(self):
        """Удаление всех записей из БД"""

        cursor = self.conn.cursor()

        cursor.execute("""
            DELETE FROM temperatures
        """)

        self.conn.commit()

    def close(self):
        """Закрытие соединения с БД"""
        try:
            self.conn.close()
            logging.info("База данных закрыта")

        except Exception as error:
            logging.error(
                f"Ошибка закрытия БД: {error}"
            )
