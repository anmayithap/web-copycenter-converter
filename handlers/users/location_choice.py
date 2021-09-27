from aiogram import types
from aiogram.dispatcher import FSMContext

from handlers.users.CopyCenterPolling import PollingEditor, PaginatorEditor
from keyboards.inline.InlinePollingCallBackDatas import method_choice_call_back_data, object_choice_call_back_data
from utils.db_api.db_editor import CityIsNotExists
from utils.misc.geolocation_city_search import geoloc_city_search
from utils.misc.nearest_location_searcher import nearest_point_searcher
from loader import dp
from utils.db_api.db_editor import DataBaseEditor
from states import CopyCenterState


class LocationSelection:
    def __init__(self, city, street, house):
        self.__city = city
        self.__street = street
        self.__house = house

    def select_settings(self):
        street_text = "Улица не определена"
        house_text = "Дом не определен"
        returning_text = '{city}, {street}, {house}'
        if self.__street == street_text and self.__house == house_text or self.__street == street_text:
            return returning_text.format(city=self.__city, street=street_text.lower(), house=house_text.lower()), (
                self.__city,)
        elif self.__house == house_text:
            return returning_text.format(city=self.__city, street=f'улица {self.__street}', house=house_text.lower()), (
                self.__city, self.__street)
        else:
            return returning_text.format(city=self.__city, street=f'улица {self.__street}',
                                         house=f'дом {self.__house}'), (self.__city, self.__street, self.__house)


@dp.callback_query_handler(method_choice_call_back_data.filter(method_name='location'),
                           state=CopyCenterState.choice_methods)
async def choice_location(call: types.CallbackQuery, state: FSMContext):
    await PollingEditor().data_base_worker('insert_user', user_id=call.message.chat.id,
                                           user_name=call.message.chat.full_name)
    markup = types.InlineKeyboardMarkup()
    await call.message.edit_text(text=PollingEditor().get_message('choice_location'),
                                 reply_markup=markup.add(PaginatorEditor().cancel))
    await state.set_state(CopyCenterState.wait_location)
    await state.update_data(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.message_handler(content_types=['location'], state=CopyCenterState.wait_location)
async def get_location(message: types.Message, state: FSMContext):
    user_location = [message.location.latitude, message.location.longitude, message.location]
    city, street, house = geoloc_city_search(user_location[0], user_location[1])
    data = await state.get_data()
    chat_id, message_id = data['chat_id'], data['message_id']
    text, markup = '', types.InlineKeyboardMarkup()
    await message.delete()
    try:
        text, location_info = LocationSelection(city, street, house).select_settings()
        await PollingEditor().data_base_worker('check_city_instance', city=city)
        nearest_button = types.InlineKeyboardButton(text='Ближайший', callback_data=method_choice_call_back_data.new(
            method_name='nearest'))
        if len(location_info) == 1:
            continue_button = types.InlineKeyboardButton(text='Далее',
                                                         callback_data=object_choice_call_back_data.new(
                                                             object_name=location_info[0],
                                                             object_polling='True'))
            await state.set_state(CopyCenterState.city)
        elif len(location_info) == 2:
            continue_button = types.InlineKeyboardButton(text='Далее',
                                                         callback_data=object_choice_call_back_data.new(
                                                             object_name=location_info[1],
                                                             object_polling='True'))
            await state.update_data(city=location_info[0])
            await state.set_state(CopyCenterState.street)
        elif len(location_info) == 3:
            continue_button = types.InlineKeyboardButton(text='Далее',
                                                         callback_data=object_choice_call_back_data.new(
                                                             object_name=location_info[2],
                                                             object_polling='True'))
            await state.update_data(city=location_info[0], street=location_info[1])
            await state.set_state(CopyCenterState.house)
        text = PollingEditor().get_message('location_good_request').format(city=text)
        markup.add(continue_button).add(nearest_button)
    except CityIsNotExists:
        text = PollingEditor().get_message('location_bad_request').format(city=city)
    await state.update_data(user_location=user_location)
    await dp.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text,
                                   reply_markup=markup.add(PaginatorEditor().cancel))
    await PollingEditor().add_message_id(state, message_id)


@dp.callback_query_handler(method_choice_call_back_data.filter(method_name='nearest'), state='*')
async def nearest_printers(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_location = data['user_location']
    db = DataBaseEditor()
    printers_identifications = db.get_all_coords_of_printers()
    db.close_connection()
    min_delta, nearest_coord = 100.01, 0
    markup = types.InlineKeyboardMarkup()
    for row_index in range(len(printers_identifications)):
        delta = nearest_point_searcher(user_location, printers_identifications[row_index])
        if delta < min_delta:
            min_delta = delta
            nearest_coord = printers_identifications[row_index]
    printer_id = await PollingEditor().data_base_worker('get_printer_id_by_coords', x_coord=nearest_coord[0],
                                                        y_coord=nearest_coord[1])
    printer_info, double_could, printer_cost = await PollingEditor().create_printer_card(printer_id)
    edit_text = PollingEditor().get_favorite_printer_card(printer_info)
    markup.add(types.InlineKeyboardButton(f'ID - {printer_id}',
                                          callback_data=f'download:{double_could}:{printer_cost}'))
    await state.set_state(CopyCenterState.download)
    await call.message.edit_text(text=edit_text, reply_markup=markup.add(PaginatorEditor().cancel))
    await state.update_data(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await PollingEditor().add_message_id(state, call.message.message_id)
