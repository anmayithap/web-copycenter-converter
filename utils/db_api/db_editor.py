import logging
import sqlite3
import pathlib
from utils.db_api.init_database import DataBaseInitializer, LOGGING_MESSAGES
from settings import DATABASE_PATH


class CityIsNotExists(Exception):
    pass


class PrinterIDExists(Exception):
    pass


class PrintersNotInFavoriteList(Exception):
    pass


class DataBaseEditor(DataBaseInitializer):
    def __init__(self):
        try:
            self.connection = sqlite3.connect(DATABASE_PATH)
            self.connection.create_collation('NOCASE', self.ignore_case_collation)
            logging.info(LOGGING_MESSAGES['connection'])
        except sqlite3.Error as SQLiteError:
            logging.warning(LOGGING_MESSAGES['connection_error'], SQLiteError)

    def insert_user(self, values):
        user_id, user_name = values
        self.connection.execute("INSERT INTO users (USER_ID, USER_NAME) VALUES (?, ?)", (user_id, user_name))
        self.connection.commit()

    def insert_user_file(self, values):
        self.connection.execute("INSERT INTO users_has_files (REQUEST_ID, "
                                "PAGES_COUNT, FILE_PATH, FILE_TYPE, DOUBLE_PAGES_OPTION, "
                                "REQUEST_TIME, REQUEST_DATE, MUST_PAGES, COPY_COUNT, DONE)"
                                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
        self.connection.commit()

    def select_all_objects(self, values):
        object_name, kwargs = values
        query = f"SELECT {object_name} FROM printers"
        if len(kwargs) > 0:
            if len(kwargs) == 1:
                query += f' WHERE CITY=?;'
            elif len(kwargs) == 2:
                objects = self.connection.execute(
                    "SELECT HOUSE, LETTER, BUILDING_BODY FROM printers WHERE STREET=? AND CITY=?",
                    list(kwargs.values())).fetchall()
                new_objects = []
                for obj in objects:
                    house, letter, building_body = obj
                    if building_body == 'NULL' or building_body == 0:
                        building_body = 'отсутствует'
                    if letter == 'NULL':
                        letter = ''
                    new_objects.append((f'{house}{letter}, корпус {building_body}',))
                return new_objects
        objects = self.connection.execute(query, tuple(kwargs.values())).fetchall()
        return objects

    def select_requests(self, user_id):
        return self.connection.execute("SELECT REQUEST_ID FROM users WHERE USER_ID=?", (user_id,)).fetchall()

    def delete_user_rows(self, user_id):
        requests = self.select_requests(user_id)
        self.connection.execute("DELETE FROM users where USER_ID=?", (user_id,))
        self.connection.commit()
        if not requests:
            return None
        for request in requests:
            try:
                try:
                    file_path = self.connection.execute("SELECT FILE_PATH FROM users_has_files where REQUEST_ID=?",
                                                        (request[0],)).fetchall()[0][0]
                    if pathlib.Path.exists(pathlib.Path(file_path)):
                        pathlib.Path.unlink(pathlib.Path(file_path))
                except IndexError:
                    logging.warning(IndexError)
            except sqlite3.Error as SQLiteError:
                logging.warning(SQLiteError)
            try:
                self.connection.execute("DELETE FROM users_has_files WHERE REQUEST_ID=?", (request[0],))
                self.connection.commit()
            except sqlite3.InterfaceError as SQLiteError:
                logging.warning(SQLiteError)
                break
            return True

    def get_all_info_about_printer(self, values):
        city, street, house = values
        normal_house = ''
        for alpha in house:
            if alpha.isdigit():
                normal_house += alpha
            else:
                break
        values = (city, street, int(normal_house))
        return self.connection.execute(
            "SELECT PRINTER_ID, PRINTER_NAME, MARK,"
            " COST_BY_LIST, COULD_DOUBLE from printers WHERE CITY=? AND STREET=? AND HOUSE=?",
            values).fetchall()

    def get_all_about_printer_by_id(self, values):
        printer_info = self.connection.execute(
            "SELECT PRINTER_NAME, MARK, COST_BY_LIST, COULD_DOUBLE, CITY, STREET, HOUSE, LETTER, BUILDING_BODY"
            " FROM printers WHERE PRINTER_ID=?",
            values).fetchall()
        return printer_info[0]

    @staticmethod
    def __check_count_of_symbol(symbol, str_range):
        symbol_count = len([str_symbol for str_symbol in str_range if str_symbol == symbol])
        current_range_without_symbol = str_range.split(symbol)
        if symbol_count + 1 != len(current_range_without_symbol) and symbol in str_range:
            return False, []
        return True, current_range_without_symbol

    @classmethod
    def __check_pages_range(cls, connection, request_id, pages_count):
        result_range = ''
        current_range = connection.execute("SELECT MUST_PAGES FROM users_has_files where REQUEST_ID=?;",
                                           (request_id,)).fetchone()
        answer, current_range_without_comma = cls.__check_count_of_symbol(',', current_range[0])
        if current_range[0] == 'Весь файл':
            return pages_count
        if not answer:
            return answer
        for range_element in current_range_without_comma:
            answer, without_comma_and_dash = cls.__check_count_of_symbol('-', range_element)
            if not answer:
                return answer
            without_comma_and_dash = list(map(int, without_comma_and_dash))
            if len(without_comma_and_dash) == 1:
                result_range += (' ' + str(without_comma_and_dash[0]) + ' ')
            else:
                dash_range = [number for number in range(without_comma_and_dash[0], without_comma_and_dash[1] + 1)]
                sorted_dash_range = sorted(dash_range)
                if dash_range != sorted_dash_range:
                    return False
                str_dash_range = ' ' + ' '.join(list(map(str, dash_range)))
                result_range += str_dash_range
        split_range = sorted(list(map(int, list(set(result_range.split())))))
        result_range = list(map(int, result_range.split()))
        if split_range != result_range:
            return False
        return current_range[0]

    def __update_must_pages(self, request_id):
        self.connection.execute("UPDATE users_has_files SET MUST_PAGES='Весь файл' WHERE REQUEST_ID=?",
                                request_id)
        self.connection.commit()

    def get_pages_count(self, values):
        request_id = self.connection.execute("SELECT REQUEST_ID FROM users where USER_ID=?;", values).fetchone()
        pages_count = self.connection.execute("SELECT PAGES_COUNT FROM users_has_files WHERE REQUEST_ID=?",
                                              request_id).fetchone()
        answer_of_check = self.__check_pages_range(connection=self.connection, request_id=request_id[0],
                                                   pages_count=pages_count[0])
        if isinstance(answer_of_check, int):
            return True, answer_of_check
        elif isinstance(answer_of_check, str):
            answer_without_comma = answer_of_check.split(',')
            range_count = 0
            for number in answer_without_comma:
                if '-' not in number:
                    if int(number) > pages_count[0]:
                        self.__update_must_pages(request_id)
                        return False, pages_count[0]
                    range_count += 1
                else:
                    range_without_dash = number.split('-')
                    range_without_dash = list(map(int, range_without_dash))
                    if range_without_dash[1] > pages_count[0]:
                        self.__update_must_pages(request_id)
                        return False, pages_count[0]
                    range_count += (range_without_dash[1] - range_without_dash[0] + 1)
            return True, range_count
        self.__update_must_pages(request_id)
        return False, answer_of_check

    def insert_user_params(self, values):
        copy_count, pages_range, double_could, user_id = values
        request_id = self.connection.execute("SELECT REQUEST_ID FROM users WHERE USER_ID=?;", (user_id,)).fetchone()
        if double_could == 'Да':
            double_could = 1
        else:
            double_could = 0
        self.connection.execute(
            "UPDATE main.users_has_files SET COPY_COUNT=?, MUST_PAGES=?, DOUBLE_PAGES_OPTION=? WHERE REQUEST_ID=?",
            (copy_count, pages_range, double_could, request_id[0]))
        self.connection.commit()

    def check_favorite_printer(self, values):
        printers_id = self.connection.execute("SELECT PRINTER_ID FROM FAVORITE_PRINTERS WHERE USER_ID=?",
                                              values).fetchall()
        if not printers_id:
            raise PrintersNotInFavoriteList
        else:
            return [_[0] for _ in printers_id]

    def insert_to_favorite_list(self, values):
        printer_id, user_id = values
        printers_id = self.connection.execute("SELECT PRINTER_ID FROM FAVORITE_PRINTERS WHERE USER_ID=?",
                                              (user_id,)).fetchall()
        printers_id = [_[0] for _ in printers_id]
        if printer_id in printers_id:
            raise PrinterIDExists
        else:
            self.connection.execute("INSERT INTO FAVORITE_PRINTERS (PRINTER_ID, USER_ID) VALUES (?, ?)", values)
            self.connection.commit()

    def check_city_instance(self, values):
        answer = self.connection.execute("SELECT * FROM printers WHERE CITY=?", values).fetchall()
        if not answer:
            raise CityIsNotExists
        return True

    def get_all_coords_of_printers(self):
        printers_coords = self.connection.execute("SELECT X_COORDINATE, Y_COORDINATE FROM printers;").fetchall()
        return printers_coords

    def get_printer_id_by_coords(self, values):
        printer_id = self.connection.execute("SELECT PRINTER_ID FROM printers WHERE X_COORDINATE=? AND Y_COORDINATE=?",
                                             values).fetchone()
        return printer_id[0]

    def close_connection(self):
        self.connection.close()
