import sqlite3
from settings import DATABASE_PATH
import logging

LOGGING_MESSAGES = {
    'connection': '!!! Database connecting !!!',
    'version': '!!! SQLite version - ',
    'connection_error': '!!! Connection to database error !!!',
    'init_tables': '!!! Creating tables if not exists !!!',
    'created_tables': '!!! Tables created !!!',
}


class DataBaseInitializer:
    def __init__(self):
        try:
            self.connection = sqlite3.connect(DATABASE_PATH)
            self.connection.create_collation('NOCASE', self.ignore_case_collation)
            self.connection.create_function('LOWER', 1, self.lower_case)
            self.connection.create_function('UPPER', 1, self.upper_case)
            logging.info(LOGGING_MESSAGES['connection'])
            sqlite_version = self.connection.cursor().execute("SELECT sqlite_version();")
            logging.info(LOGGING_MESSAGES['version'] + f'{sqlite_version.fetchall()[0][0]} !!!')
            self.connection.cursor().close()
            logging.info(LOGGING_MESSAGES['init_tables'])
            self.__create_tables_if_not_exists(self.connection)
            logging.info(LOGGING_MESSAGES['created_tables'])
        except sqlite3.Error as SQLiteError:
            logging.warning(LOGGING_MESSAGES['connection_error'], SQLiteError)

    @staticmethod
    def lower_case(value_):
        return value_.lower()

    @staticmethod
    def upper_case(value_):
        return value_.upper()

    @staticmethod
    def ignore_case_collation(data_base_value, collation_value):
        if data_base_value.lower() == collation_value.lower():
            return 0
        elif data_base_value.lower() < collation_value.lower():
            return -1
        else:
            return 1

    @classmethod
    def __create_tables_if_not_exists(cls, connection: sqlite3.connect):
        connection.executescript("""
                                CREATE TABLE IF NOT EXISTS users(
                                    REQUEST_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                    USER_ID INTEGER NOT NULL,
                                    USER_NAME TEXT NOT NULL DEFAULT '');
                                
                                CREATE TABLE IF NOT EXISTS users_has_files(
                                    FILE_ID INTEGER PRIMARY KEY AUTOINCREMENT ,
                                    REQUEST_ID INTEGER NOT NULL,
                                    PAGES_COUNT INTEGER NOT NULL DEFAULT 0,
                                    FILE_PATH TEXT NOT NULL DEFAULT '',
                                    FILE_TYPE TEXT NOT NULL DEFAULT '',
                                    DOUBLE_PAGES_OPTION INTEGER(1) NOT NULL DEFAULT 0,
                                    REQUEST_TIME TEXT NOT NULL DEFAULT '',
                                    REQUEST_DATE TEXT NOT NULL DEFAULT '',
                                    MUST_PAGES TEXT NOT NULL DEFAULT '',
                                    COPY_COUNT INTEGER NOT NULL DEFAULT 0,
                                    DONE INTEGER(1) NOT NULL DEFAULT 0
                                    CHECK ( DOUBLE_PAGES_OPTION < 2 AND DOUBLE_PAGES_OPTION >= 0 ),
                                    CHECK ( DONE < 2 AND DONE >= 0 ),
                                    FOREIGN KEY (REQUEST_ID) REFERENCES users(REQUEST_ID)
                                );
                                
                                CREATE TABLE IF NOT EXISTS printers(
                                    PRINTER_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                    PRINTER_IP_ADDRESS TEXT NOT NULL UNIQUE DEFAULT '',
                                    PRINTER_NAME TEXT NOT NULL DEFAULT '',
                                    CITY TEXT NOT NULL DEFAULT '' COLLATE NOCASE,
                                    STREET TEXT NOT NULL DEFAULT '' COLLATE NOCASE,
                                    HOUSE INTEGER NOT NULL DEFAULT 0,
                                    LETTER TEXT NOT NULL DEFAULT NULL COLLATE NOCASE,
                                    BUILDING_BODY INTEGER NOT NULL DEFAULT NULL,
                                    MARK TEXT NOT NULL DEFAULT '',
                                    COULD_DOUBLE INTEGER(1) NOT NULL DEFAULT 0,
                                    X_COORDINATE DECIMAL(9, 6) NOT NULL DEFAULT 0,
                                    Y_COORDINATE DECIMAL(9, 6) NOT NULL DEFAULT 0,
                                    COST_BY_LIST DECIMAL(10, 2) NOT NULL DEFAULT 0,
                                    CONSTRAINT ADDRESS UNIQUE (CITY, STREET, HOUSE, LETTER, BUILDING_BODY)
                                );
                                
                                CREATE TABLE IF NOT EXISTS FAVORITE_PRINTERS(
                                    PRINTER_ID INTEGER NOT NULL,
                                    USER_ID INTEGER NOT NULL,
                                    FOREIGN KEY (PRINTER_ID) REFERENCES printers(PRINTER_ID)
                                );
                                """)
        connection.commit()
        connection.close()
