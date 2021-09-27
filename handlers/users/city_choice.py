from aiogram import types
from aiogram.dispatcher import FSMContext

from handlers.users.CopyCenterPolling import PollingEditor, PaginatorEditor, pagination
from keyboards.inline.InlinePollingCallBackDatas import method_choice_call_back_data, pagination_choice_call_back_data, \
    object_choice_call_back_data
from loader import dp
from states import CopyCenterState


@dp.callback_query_handler(method_choice_call_back_data.filter(method_name='city'),
                           state=CopyCenterState.choice_methods)
async def choice_city(call: types.CallbackQuery, state: FSMContext):
    await PollingEditor().data_base_worker('insert_user', user_id=call.message.chat.id,
                                           user_name=call.message.chat.full_name)
    cites = list(set([city[0] for city in
                      await PollingEditor().data_base_worker('select_all_objects', object_name='CITY', kwargs={})]))
    markup = PaginatorEditor(cites, 3, 3).get_markup_first()
    await state.update_data(menu_choice='city', cites=cites,
                            paginator=PaginatorEditor(cites, 3, 3))
    sending_message = PollingEditor.get_message('chosen_city_success')
    await call.message.edit_text(sending_message, reply_markup=markup)
    await state.set_state(CopyCenterState.city)
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.callback_query_handler(pagination_choice_call_back_data.filter(call_back='pagination'), state=CopyCenterState.city)
async def city_pagination(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    markup = await pagination(state, 'cites', int(callback_data['number']))
    await call.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                             reply_markup=markup)
    await state.set_state(state=CopyCenterState.city)
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.callback_query_handler(object_choice_call_back_data.filter(object_polling='True'), state=CopyCenterState.city)
async def street_choice(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    city = callback_data['object_name']
    streets = list(set(await PollingEditor().data_base_worker('select_all_objects',
                                                              object_name='STREET', kwargs=dict(city=city))))
    markup = PaginatorEditor(streets, 3, 3).get_markup_first()
    sending_message = PollingEditor.get_message('chosen_street_success')
    await call.bot.edit_message_text(chat_id=call.message.chat.id,
                                     message_id=call.message.message_id,
                                     text=sending_message,
                                     reply_markup=markup)
    await state.update_data(city=city, streets=streets, paginator=PaginatorEditor(streets, 3, 3))
    await state.set_state(CopyCenterState.street)
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.callback_query_handler(pagination_choice_call_back_data.filter(call_back='pagination'),
                           state=CopyCenterState.street)
async def street_pagination(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    markup = await pagination(state, 'streets', int(callback_data['number']))
    await call.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                             reply_markup=markup)
    await state.set_state(state=CopyCenterState.street)
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.callback_query_handler(object_choice_call_back_data.filter(object_polling='True'),
                           state=CopyCenterState.street)
async def house_choice(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    city, street = data.get('city'), callback_data.get('object_name')
    houses = list(set(await PollingEditor().data_base_worker('select_all_objects', object_name='HOUSE',
                                                             kwargs=dict(street=street, city=city))))
    markup = PaginatorEditor(houses, 3, 3).get_markup_first()
    sending_message = PollingEditor.get_message('chosen_house_success')
    await call.bot.edit_message_text(chat_id=call.message.chat.id,
                                     message_id=call.message.message_id,
                                     text=sending_message,
                                     reply_markup=markup)
    await state.update_data(street=street, city=city, houses=houses,
                            paginator=PaginatorEditor(houses, 3, 3))
    await state.set_state(CopyCenterState.house)
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.callback_query_handler(pagination_choice_call_back_data.filter(call_back='pagination'),
                           state=CopyCenterState.house)
async def house_pagination(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    markup = await pagination(state, 'houses', int(callback_data['number']))
    await call.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                             reply_markup=markup)
    await state.set_state(state=CopyCenterState.house)
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.callback_query_handler(object_choice_call_back_data.filter(object_polling='True'), state=CopyCenterState.house)
async def get_user_file(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    city, street, house = data.get('city'), data.get('street'), callback_data.get('object_name')
    printer_info = await PollingEditor().data_base_worker('get_all_info_about_printer', city=city,
                                                          street=street, house=house)
    printer_id, printer_name, printer_mark, printer_cost, double_could = printer_info[0]
    if int(double_could):
        text_double_could = 'Да'
    else:
        text_double_could = 'Нет'
    printer_info = (printer_name, text_double_could, city, street, house, printer_mark, printer_cost)
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    download = InlineKeyboardButton('Загрузить', callback_data='download')
    await call.bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=PollingEditor().get_printer_card(printer_info),
        reply_markup=InlineKeyboardMarkup().add(download).add(PaginatorEditor().cancel).add(
            PaginatorEditor().add_to_favorite_list)
    )
    await state.update_data(message_id=call.message.message_id, chat_id=call.message.chat.id,
                            printer_id=printer_id, double_could=double_could, printer_cost=printer_cost,
                            printer_info=printer_info)
    await state.set_state(CopyCenterState.download)
    await PollingEditor().add_message_id(state, call.message.message_id)
