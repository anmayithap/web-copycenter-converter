from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.inline.InlinePollingCallBackDatas import object_choice_call_back_data, \
    pagination_choice_call_back_data, cancel_choice_call_back_data, \
    number_choice_call_back_data
import math
import numpy as np


class Paginator:
    __PAGINATION_DICT = dict()

    def __init__(self, objects, rows_width=3, col_height=3):
        self.__PAGINATION_DICT.clear()
        self._objects = objects
        self._row_width = rows_width
        self._col_height = col_height
        self._objects_count = len(self._objects)
        self._pagination_numbers = self.__calculate_pages_count(self._objects_count, self._row_width * self._col_height)
        self._pag_objects, self.__PAGINATION_DICT = self.__add_pagination(
            self._objects, self._pagination_numbers, self._col_height, self._row_width
        )
        self.__push_pagination()

    @staticmethod
    def __calculate_pages_count(objects_count, count_in_one_page):
        return math.ceil(objects_count / count_in_one_page)

    @classmethod
    def __add_pagination(cls, objects, pagination, col_height, row_width):
        pagination_numbers = [number for number in range(1, pagination + 1)]
        for number in pagination_numbers:
            cls.__PAGINATION_DICT.update({number: {}})
        split_objects = []
        row_max = col_height * row_width
        for index in range(pagination):
            tmp_objects = np.array(objects[index * row_max:index * row_max + row_max])
            try:
                tmp_objects.shape = (col_height, row_width)
            except ValueError:
                try:
                    tmp_objects.shape = (-1, row_width)
                except ValueError:
                    tmp_objects.shape = (1, -1)
            split_objects.append(tmp_objects.tolist())
        return split_objects, cls.__PAGINATION_DICT

    @staticmethod
    def __update_pagination_dict(pagination_dict, **kwargs):
        pagination_dict[kwargs['index']] = kwargs['pag_objects'][kwargs['pag_index']]
        pagination_dict[kwargs['index']].append([kwargs['left'], kwargs['center'], kwargs['right']])
        return pagination_dict

    def __push_pagination(self):
        if self._pagination_numbers == 1:
            self.__PAGINATION_DICT = self.__update_pagination_dict(self.__PAGINATION_DICT,
                                                                   index=self._pagination_numbers,
                                                                   pag_objects=self._pag_objects, pag_index=0, left='-',
                                                                   right='-', center=f'-{self._pagination_numbers}-')
        elif self._pagination_numbers > 1:
            for key in self.__PAGINATION_DICT:
                if key == 1:
                    self.__PAGINATION_DICT = self.__update_pagination_dict(self.__PAGINATION_DICT,
                                                                           index=key, pag_objects=self._pag_objects,
                                                                           pag_index=key - 1, left='-',
                                                                           right=f'{key + 1} >',
                                                                           center=f'-{key}-')
                elif key == self._pagination_numbers:
                    self.__PAGINATION_DICT = self.__update_pagination_dict(self.__PAGINATION_DICT,
                                                                           index=key, pag_objects=self._pag_objects,
                                                                           pag_index=key - 1, left=f'< {key - 1}',
                                                                           right='-',
                                                                           center=f'-{key}-')
                else:
                    self.__PAGINATION_DICT = self.__update_pagination_dict(self.__PAGINATION_DICT,
                                                                           index=key, pag_objects=self._pag_objects,
                                                                           pag_index=key - 1, left=f'< {key - 1}',
                                                                           right=f'{key + 1} >',
                                                                           center=f'-{key}-')

    def get_pagination_dict(self):
        return self.__PAGINATION_DICT


class InlineKeyBoard:
    __INLINE_KEY_BOARD_BUTTONS = {
        'objects': dict()
    }

    def cites_pagination(self, objects, row_count, col_count):
        paginator = Paginator(objects, rows_width=row_count, col_height=col_count)
        pagination_dict = paginator.get_pagination_dict()
        for item in pagination_dict:
            objects_buttons = pagination_dict[item][:-1]
            pagination_buttons = pagination_dict[item][-1]
            new_objects_buttons = []
            for row in objects_buttons:
                new_row = []
                for object_row in row:
                    new_row.append(
                        InlineKeyboardButton(text=object_row,
                                             callback_data=object_choice_call_back_data.new(object_name=object_row,
                                                                                            object_polling=True)))
                new_objects_buttons.append(new_row)
            new_pagination_buttons = [txt for txt in pagination_buttons if txt != '-']
            if len(new_pagination_buttons) != 1:
                row = []
                for txt in new_pagination_buttons:
                    number = ''
                    for str_item in txt:
                        if str_item.isdigit():
                            number += str_item
                    row.append(InlineKeyboardButton(txt, callback_data=pagination_choice_call_back_data.new(
                        call_back='pagination',
                        number=number)))
                new_objects_buttons.append(row)
            self.__INLINE_KEY_BOARD_BUTTONS['objects'][item] = new_objects_buttons

    def get_inline_keyboards(self, option, number):
        return InlineKeyboardMarkup(row_width=2, inline_keyboard=self.__INLINE_KEY_BOARD_BUTTONS[option][number])


def create_inline_keyboard_button(text, callback_data):
    return InlineKeyboardButton(text=text,
                                callback_data=cancel_choice_call_back_data.new(method_name=callback_data))


def create_keyboard_with_numbers(text, callback_data):
    return InlineKeyboardMarkup(text=text,
                                callback_data=number_choice_call_back_data.new(text='keyboard_with_numbers',
                                                                               number=callback_data,
                                                                               mean=text))


class MenuInlineKeyBoard:
    __INLINE_KEY_BOARD_BUTTONS = {
        'choice_methods': {
            'keyboard_buttons': [[create_inline_keyboard_button('Выбрать город 🏢', 'city'),
                                  create_inline_keyboard_button('Местоположение 📍', 'location')],
                                 [create_inline_keyboard_button('По ID принтера 🆔', 'id'),
                                  create_inline_keyboard_button('Избранные 📌', 'favorite_list')]
                                 ]
        },
        'lets_print_methods': {
            'keyboard_buttons': [[create_inline_keyboard_button('Напечатать', 'print'),
                                  create_inline_keyboard_button('Задать параметры печати', 'edit_options')],
                                 [create_inline_keyboard_button('Выйти в меню ❌', 'cancel')]
                                 ]
        },
        'lets_print_methods_without_edit_params': {
            'keyboard_buttons': [
                [create_inline_keyboard_button('Напечатать', 'print')],
                [create_inline_keyboard_button('Выйти в меню ❌', 'cancel')]
            ]
        },
        'options_menu': {
            'keyboard_buttons': [
                [create_inline_keyboard_button('Выбрать количество копий', "copy_count")],
                [create_inline_keyboard_button('Двухсторонняя печать', 'could_double'),
                 create_inline_keyboard_button('Выбрать диапазон страниц', 'pages_range')],
                [create_inline_keyboard_button('Готово', 'submit')]]
        },
        'page_range_menu': {
            'keyboard_buttons': [
                [create_keyboard_with_numbers('1', '1'), create_keyboard_with_numbers('2', '2'),
                 create_keyboard_with_numbers('3', '3')],
                [create_keyboard_with_numbers('4', '4'), create_keyboard_with_numbers('5', '5'),
                 create_keyboard_with_numbers('6', '6')],
                [create_keyboard_with_numbers('7', '7'), create_keyboard_with_numbers('8', '8'),
                 create_keyboard_with_numbers('9', '9')],
                [create_keyboard_with_numbers(',', '10'), create_keyboard_with_numbers('0', '0'),
                 create_keyboard_with_numbers('-', '11')],
                [create_keyboard_with_numbers('CE', '12')]
            ]
        },
        'double_could_menu': {
            'keyboard_buttons': [
                [create_keyboard_with_numbers('Да', '1'),
                 create_keyboard_with_numbers('Нет', '0')]
            ]
        }
    }

    @classmethod
    def get_inline_keyboards(cls, menu_part):
        return InlineKeyboardMarkup(row_width=3,
                                    inline_keyboard=cls.__INLINE_KEY_BOARD_BUTTONS[menu_part]['keyboard_buttons'])
