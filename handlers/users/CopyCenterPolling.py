from aiogram import types
from loader import dp
from states.CopyCenterStates import CopyCenterState
from aiogram.dispatcher.storage import FSMContext
from aiogram.dispatcher.filters import Command
from keyboards.inline.InlinePollingKeyBoards import InlineKeyBoard, MenuInlineKeyBoard
from keyboards.inline.InlinePollingCallBackDatas import method_choice_call_back_data, cancel_choice_call_back_data, \
    number_choice_call_back_data
from utils.convert_api.editor import FileTypeIsNotExists
from utils.db_api.db_editor import DataBaseEditor, PrinterIDExists
from settings import DOCUMENT_DIR, IMAGE_DIR


class PollingEditor:
    EMOJI_LIST = {'sad': '☹', 'great': '😁', 'document': '📃', 'city': '🏢', 'location': '📍', 'cancel': '❌',
                  'back': '🔙', 'easy': '👇', 'some_sad': '😟', 'printer': ' 🖨'}

    FILE_TYPES_LIST = ['PDF', 'DOC', 'DOCX', 'XLS', 'XLSX', 'PPT', 'PPTX', 'PNG',
                       'JPG', 'JPEG', 'BMP', 'EPS', 'GIF', 'TXT', 'RTF', 'HTML']

    DOCUMENT_TYPES_LIST = ['PDF', 'DOC', 'DOCX', 'XLS', 'XLSX', 'PPT',
                           'PPTX', 'TXT', 'RTF', 'HTML']

    IMAGE_TYPES_LIST = list(set(FILE_TYPES_LIST).difference(set(DOCUMENT_TYPES_LIST)))

    @classmethod
    def get_message(cls, state):
        message_list = {
            '/start_copy_center': f'Хорошо, приступим к заполнению необходимых данных {cls.EMOJI_LIST["great"]}\n'
                                  f'Я поддерживаю следующие форматы файлов {cls.FILE_TYPES_LIST}, будьте '
                                  f'внимательны!\n'
                                  f'Для начала укажи свой город {cls.EMOJI_LIST["city"]}\n'
                                  f'Или передайте свое местоположение {cls.EMOJI_LIST["location"]}\n',

            'choice_location': f'Передайте свое местоположение',

            'choice_city_bad_button': f'Вы должны выбрать кнопку клавиатуры {cls.EMOJI_LIST["easy"]},\n'
                                      f'Иначе я не смогу вам помочь {cls.EMOJI_LIST["some_sad"]}.',

            'chosen_city_success': f'Список городов, в которых есть принтеры {cls.EMOJI_LIST["printer"]}:',

            'chosen_street_success': f'Список улиц этого города, в которых есть принтеры {cls.EMOJI_LIST["printer"]}:',

            'chosen_house_success': f'Список домов, в которых есть принтеры {cls.EMOJI_LIST["printer"]}:',

            'download_file': f'Отлично! Отправьте или перешлите мне свой файл для проверки\n\n'
                             f'Напомню: {cls.FILE_TYPES_LIST}',

            'download_file_success': 'Файл успешно обработан и загружен на сервер\n'
                                     'Приступим к выбору параметров печати, либо же печатаем сразу?',

            'download_file_error': "К сожалению я не могу принять ваш файл."
                                   "Попробуйте загрузить другой файл, или попробуйте заново."
                                   "Ошибка обработки файла: \n",
            'can_edit_params': 'Доступные параметры печати:',
            'copy_count_edit': 'Введите количество копий:',
            'double_could_edit': 'Двухсторонняя печать:',
            'page_range_edit': 'Введите диапазон страниц:',
            'lets_pay_for_document': 'Хорошо, для начала оплатите услугу:',
            'choice_id': 'Пожалуйста введите ID принтера:',
            'choice_id_not_found': "Принтера с данным ID, не существует\n"
                                   "Попробуйте заново, либо выберите другой способ",
            'favorite_list_is_empty': f'У вас еще нет избранных принтеров',
            'location_bad_request': 'Если ваш населенный пункт {city}, то на данный момент\n'
                                    'он не обслуживается нашим сервисом облачной печати.',
            'location_good_request': 'Если ваш населенный пункт {city}, то нажмите кнопку далее.',
        }
        return message_list[state]

    @staticmethod
    def get_printer_card(printer_info):
        printer_name, text_double_could, city, street, house, printer_mark, printer_cost = printer_info
        text = f"Карточка принтера:\n" \
               f"Название: {printer_name}\n" \
               f"Возможность двусторонней печати: {text_double_could}\n" \
               f"Адрес: г. {city}, ул. {street}, д. {house} - {printer_mark}\n" \
               f"Цена за лист: {printer_cost} руб.\n\n" \
               f'Теперь вам необходимо загрузить файл {PollingEditor().EMOJI_LIST["document"]}, ' \
               f'для этого нажмите на соответсвующую кнопку. {PollingEditor().EMOJI_LIST["easy"]}'
        return text

    @staticmethod
    def get_favorite_printer_card(printer_info):
        printer_id, printer_name, text_double_could, city, street, house, printer_mark, printer_cost = printer_info
        text = f'Карточка принтера {printer_id}\n' \
               f'Название: {printer_name}\n' \
               f'Возможность двусторонней печати: {text_double_could}\n' \
               f'Адрес: г. {city}, ул. {street}, д. {house} - {printer_mark}\n' \
               f'Цена за лист: {printer_cost} руб.'
        return text

    @staticmethod
    def translate_printer_card(house, double_could, building_body, letter):
        if int(double_could):
            text_double_could = 'Да'
        else:
            text_double_could = 'Нет'
        if building_body == 'NULL' or building_body == 0:
            building_body = 'отсутствует'
        if letter == 'NULL':
            letter = ''
        house = f'{house}{letter}, корпус {building_body}'
        return house, text_double_could

    @staticmethod
    async def create_printer_card(printer_id):
        printer_info = await PollingEditor().data_base_worker('get_all_about_printer_by_id', printer_id=printer_id)
        printer_name, printer_mark, printer_cost, double_could, city, street, house, letter, building_body = printer_info
        house, text_double_could = PollingEditor().translate_printer_card(house, double_could, building_body, letter)
        printer_info = (printer_id, printer_name, text_double_could, city, street, house, printer_mark, printer_cost)
        return printer_info, double_could, printer_cost

    @staticmethod
    def get_current_print_options(double_could, pages_count, pages_range):
        current_params = f'\n\nТекущие параметры печати:\n' \
                         f'Количество копий: {pages_count}\n' \
                         f'Диапазон страниц: {pages_range}'
        try:
            if int(double_could):
                current_params += '\nДвусторонняя печать: Нет'
            else:
                current_params += '\n* Возможность двусторонней печати не доступна *'
        except ValueError:
            if double_could == 'Да':
                current_params += '\nДвухсторонняя печать: Да'
            else:
                current_params += '\nДвухсторонняя печать: Нет'
        return current_params

    @staticmethod
    async def data_base_worker(method, **kwargs):
        data_base = DataBaseEditor()
        result = data_base.__getattribute__(method)(list(kwargs.values()))
        data_base.close_connection()
        del data_base
        return result

    @staticmethod
    async def add_message_id(state: FSMContext, message_id):
        async with state.proxy() as data:
            if message_id not in data.get('another_messages_id'):
                data['another_messages_id'].append(message_id)

    @staticmethod
    def toFixed(number, literal):
        return float(f"{number:.{literal}f}")

    @classmethod
    async def get_price(cls, user_id, price_of_list):
        answer, pages_count = await cls.data_base_worker('get_pages_count', user_id=user_id)
        return answer, cls.toFixed(price_of_list * pages_count, 2)


class PaginatorEditor:
    def __init__(self, objects=None, row=None, col=None):
        from aiogram.types import InlineKeyboardButton
        if objects is not None:
            self.__paginator = InlineKeyBoard()
            self.__paginator = self.__start_pagination(paginator=self.__paginator,
                                                       objects=objects, row=row, col=col)
        self.cancel = InlineKeyboardButton('Выйти в меню ❌',
                                           callback_data=cancel_choice_call_back_data.new(method_name='cancel'))

        self.back = InlineKeyboardButton('Вернуться назад 🔙',
                                         callback_data=method_choice_call_back_data.new(method_name='edit_options'))

        self.add_to_favorite_list = InlineKeyboardButton('Добавить в избранные 📌',
                                                         callback_data=method_choice_call_back_data.new(
                                                             method_name='add_to_favorite'))

    @staticmethod
    def __start_pagination(paginator, objects, row, col):
        paginator.cites_pagination(objects=objects, row_count=row, col_count=col)
        return paginator

    def get_markup_first(self):
        markup = self.__paginator.get_inline_keyboards('objects', 1).add(self.cancel)
        return markup

    def get_markup_next_or_pre(self, pag_number):
        return self.__paginator.get_inline_keyboards('objects', pag_number).add(self.cancel)


async def pagination(state, objects_name, callback_number):
    data = await state.get_data()
    objects, paginator = data.get(f'{objects_name}'), data.get('paginator')
    await state.update_data({
        objects_name: objects,
        'paginator': paginator
    })
    return paginator.get_markup_next_or_pre(callback_number)


# Выводим первый стейт с выбором метода определения геопозиции
@dp.message_handler(Command('start_copy_center'))
async def start_polling(message: types.Message, state: FSMContext):
    inline_markup = MenuInlineKeyBoard().get_inline_keyboards(menu_part='choice_methods')
    sending_message = PollingEditor.get_message(message.text)
    await message.answer(text=sending_message, reply_markup=inline_markup)
    await CopyCenterState.first()
    await state.update_data(another_messages_id=[message.message_id, message.message_id + 1])


@dp.callback_query_handler(cancel_choice_call_back_data.filter(method_name='cancel'), state='*')
async def cancel_to_menu(call: types.CallbackQuery, state: FSMContext):
    from utils.convert_api.file_handler import clear_data_base
    data = await state.get_data()
    messages = data['another_messages_id']
    await state.finish()
    await clear_data_base(user_id=call.message.chat.id)
    sending_message = PollingEditor().get_message('/start_copy_center')
    inline_markup = MenuInlineKeyBoard().get_inline_keyboards(menu_part='choice_methods')
    await call.message.edit_text(text=sending_message, reply_markup=inline_markup)
    await CopyCenterState.first()
    await state.update_data(another_messages_id=messages)
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.callback_query_handler(method_choice_call_back_data.filter(method_name='add_to_favorite'),
                           state=CopyCenterState.download)
async def add_to_favorite_list(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    printer_id, user_id, printer_info = data['printer_id'], data['chat_id'], data['printer_info']
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('Загрузить', callback_data='download')).add(
        PaginatorEditor().cancel)
    sending_message = PollingEditor().get_printer_card(printer_info)
    try:
        await PollingEditor().data_base_worker('insert_to_favorite_list', printer_id=printer_id, user_id=user_id)
        answer = '\n\n* Принтер успешно добавлен в список избранных *'
        await call.message.edit_text(text=sending_message + answer,
                                     reply_markup=markup)
    except PrinterIDExists:
        answer = '\n\n* Данный принтер уже в списке избранных *'
        await call.message.edit_text(text=sending_message + answer,
                                     reply_markup=markup)


@dp.callback_query_handler(text_contains='download', state=CopyCenterState.download)
async def set_download_file(call: types.CallbackQuery, state: FSMContext):
    try:
        double_could, printer_price = call.data.split(':')[1:]
        await state.update_data(double_could=double_could, printer_cost=printer_price)
    except ValueError:
        pass
    await call.bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=PollingEditor().get_message('download_file'),
        reply_markup=types.InlineKeyboardMarkup().add(PaginatorEditor().cancel)
    )
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.message_handler(content_types=['document', 'photo'], state=CopyCenterState.download)
async def download_file(message: types.Message, state: FSMContext):
    from utils.convert_api.file_handler import get_image, get_document, converting_files_in_dirs
    data = await state.get_data()
    message_id, chat_id, double_could, printer_cost = data['message_id'], data['chat_id'], int(
        data['double_could']), float(data['printer_cost'])
    try:
        if message.document is None:
            downloaded_file, src = await get_image(message)
            mode = IMAGE_DIR
        else:
            document_types = PollingEditor().DOCUMENT_TYPES_LIST
            current_type = message.document.file_name.split('.')[-1].upper()
            if current_type not in document_types:
                raise FileTypeIsNotExists(current_type, document_types)
            downloaded_file, src = await get_document(message)
            mode = DOCUMENT_DIR
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file.getvalue())
        converting_files_in_dirs(mode)
        current_params = PollingEditor().get_current_print_options(double_could, 1, 'Весь файл')
        await PollingEditor().data_base_worker('insert_user_params', copy_count=1, current_range='Весь файл',
                                               could_double='Нет', user_id=message.chat.id)
        answer, price = await PollingEditor().get_price(user_id=chat_id, price_of_list=printer_cost)
        current_params += f'\n\nИтоговая стоимость {price} руб.'
        await state.update_data(price=price)
        await dp.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                       text=PollingEditor().get_message('download_file_success') + current_params,
                                       reply_markup=MenuInlineKeyBoard().get_inline_keyboards('lets_print_methods'))
        await message.delete()
        await state.set_state(CopyCenterState.choice_print_methods)
    except FileTypeIsNotExists as error:
        await message.delete()
        await dp.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                       text=PollingEditor().get_message('download_file_error') + error.__str__(),
                                       reply_markup=types.InlineKeyboardMarkup().add(PaginatorEditor().cancel))
        await state.set_state(CopyCenterState.download)


@dp.callback_query_handler(method_choice_call_back_data.filter(method_name='print'),
                           state='*')
async def get_payment(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data['price']


@dp.callback_query_handler(method_choice_call_back_data.filter(method_name='edit_options'),
                           state=CopyCenterState.choice_print_methods)
async def push_options_buttons(call: types.CallbackQuery, state: FSMContext):
    markup = MenuInlineKeyBoard().get_inline_keyboards('options_menu').add(PaginatorEditor().cancel)
    data = await state.get_data()
    if not int(data['double_could']):
        markup['inline_keyboard'][1].pop(0)
    await call.message.edit_text(text=PollingEditor().get_message('can_edit_params'), reply_markup=markup)
    await state.update_data(chat_id=call.message.chat.id, message_id=call.message.message_id,
                            selected_could_double=0, selected_copy_count=1, selected_current_range='Весь файл')
    await state.set_state(CopyCenterState.wait_edit_params)
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.callback_query_handler(method_choice_call_back_data.filter(method_name='copy_count'),
                           state=CopyCenterState.wait_edit_params)
async def input_copy_count_of_file(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await call.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                     text=PollingEditor().get_message('copy_count_edit'),
                                     reply_markup=types.InlineKeyboardMarkup().add(PaginatorEditor().back))
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.callback_query_handler(method_choice_call_back_data.filter(method_name='pages_range'),
                           state=CopyCenterState.wait_edit_params)
async def input_pages_range_of_file(call: types.CallbackQuery, state: FSMContext):
    markup = MenuInlineKeyBoard.get_inline_keyboards('page_range_menu').add(PaginatorEditor().back)
    await state.update_data(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await call.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                     text=PollingEditor().get_message('page_range_edit'),
                                     reply_markup=markup)
    await state.set_state(CopyCenterState.wait_pages_params)
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.callback_query_handler(method_choice_call_back_data.filter(method_name='could_double'),
                           state=CopyCenterState.wait_edit_params)
async def input_could_double_of_file(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(CopyCenterState.wait_double_could_params)
    markup = MenuInlineKeyBoard().get_inline_keyboards('double_could_menu').add(PaginatorEditor().back)
    await state.update_data(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await call.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                     text=PollingEditor().get_message('double_could_edit'),
                                     reply_markup=markup)
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.callback_query_handler(method_choice_call_back_data.filter(method_name='edit_options'),
                           state='*')
async def back_inline_button(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(CopyCenterState.choice_print_methods)
    markup = MenuInlineKeyBoard().get_inline_keyboards('options_menu').add(PaginatorEditor().cancel)
    data = await state.get_data()
    if not int(data['double_could']):
        markup['inline_keyboard'][1].pop(0)
    await call.message.bot.edit_message_text(chat_id=call.message.chat.id,
                                             message_id=call.message.message_id,
                                             text=PollingEditor().get_message('can_edit_params'),
                                             reply_markup=markup)
    await state.set_state(CopyCenterState.wait_edit_params)
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.callback_query_handler(number_choice_call_back_data.filter(text='keyboard_with_numbers'),
                           state=CopyCenterState.wait_pages_params)
async def page_range_controller(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    markup = MenuInlineKeyBoard.get_inline_keyboards('page_range_menu').add(PaginatorEditor().back)
    data = await state.get_data()
    chat_id, message_id = data['chat_id'], data['message_id']
    try:
        current_range = data['selected_current_range']
    except KeyError:
        current_range = 'Весь файл'
    if callback_data['number'] != '12':
        if current_range == 'Весь файл':
            current_range = callback_data['mean']
        else:
            current_range += callback_data['mean']
        await call.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                         text=PollingEditor().get_message(
                                             'page_range_edit') + f'\nВыбранный диапазон: {current_range}',
                                         reply_markup=markup)
        await state.update_data(selected_current_range=current_range)
    else:
        if current_range == 'Весь файл':
            await call.message.answer('Вы не можете удалить "ничего"')
        else:
            current_range = current_range[:-1]
            await state.update_data(selected_current_range=current_range)
            await call.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                             text=PollingEditor().get_message(
                                                 'page_range_edit') + f'\nВыбранный диапазон: {current_range}',
                                             reply_markup=markup)
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.callback_query_handler(number_choice_call_back_data.filter(text='keyboard_with_numbers'),
                           state=CopyCenterState.wait_double_could_params)
async def set_double_could_param(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    data = await state.get_data()
    chat_id, message_id = data['chat_id'], data['message_id']
    markup = MenuInlineKeyBoard.get_inline_keyboards('double_could_menu').add(PaginatorEditor().back)
    await call.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                     text=PollingEditor().get_message(
                                         'double_could_edit') + f'\n{callback_data["mean"]}',
                                     reply_markup=markup)
    await state.update_data(selected_could_double=callback_data["mean"])
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.callback_query_handler(method_choice_call_back_data.filter(method_name='submit'),
                           state='*')
async def get_current_edited_options(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    could_double, copy_count, current_range, cost_by_list = data['selected_could_double'], \
                                                            data['selected_copy_count'], \
                                                            data['selected_current_range'], float(data['printer_cost'])
    await PollingEditor().data_base_worker('insert_user_params', copy_count=copy_count, current_range=current_range,
                                           could_double=could_double, user_id=call.message.chat.id)
    answer, price = await PollingEditor().get_price(call.message.chat.id, cost_by_list)
    price = float(price) * float(copy_count)
    await state.update_data(price=price)
    if not answer:
        current_range = '* Неверно указан диапазон страниц, будет распечатан весь файл *'
    current_params = PollingEditor().get_current_print_options(could_double, copy_count, current_range)
    current_params += f'\n\nИтоговая стоимость {float(price)} руб.'
    await call.message.edit_text(current_params, reply_markup=MenuInlineKeyBoard.get_inline_keyboards(
        'lets_print_methods_without_edit_params'))
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.message_handler(lambda message: message.text.isdigit(),
                    state=CopyCenterState.wait_edit_params,
                    content_types=types.ContentTypes.TEXT)
async def get_number_of_copy_count(message: types.Message, state: FSMContext):
    data = await state.get_data()
    chat_id, message_id = data['chat_id'], data['message_id']
    copy_count = message.text
    await message.bot.edit_message_text(text=f'Текущее количество копий: {copy_count}',
                                        chat_id=chat_id, message_id=message_id,
                                        reply_markup=types.InlineKeyboardMarkup().add(PaginatorEditor().back))
    await state.update_data(selected_copy_count=copy_count)
    await message.delete()
