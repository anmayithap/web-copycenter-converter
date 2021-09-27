from aiogram import types
from aiogram.dispatcher import FSMContext

from handlers.users.CopyCenterPolling import PollingEditor, PaginatorEditor
from keyboards.inline.InlinePollingCallBackDatas import method_choice_call_back_data
from loader import dp
from states import CopyCenterState


@dp.callback_query_handler(method_choice_call_back_data.filter(method_name='id'),
                           state=CopyCenterState.choice_methods)
async def choice_by_id(call: types.CallbackQuery, state: FSMContext):
    await PollingEditor().data_base_worker('insert_user', user_id=call.message.chat.id,
                                           user_name=call.message.chat.full_name)
    await call.message.edit_text(PollingEditor().get_message('choice_id'))
    await state.update_data(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await PollingEditor().add_message_id(state, call.message.message_id)


@dp.message_handler(lambda message: message.text.isdigit(),
                    state=CopyCenterState.choice_methods)
async def send_id(message: types.Message, state: FSMContext):
    printer_id = int(message.text)
    await message.delete()
    markup = types.InlineKeyboardMarkup()
    data = await state.get_data()
    chat_id, message_id = data['chat_id'], data['message_id']
    try:
        printer_info, double_could, printer_cost = await PollingEditor().create_printer_card(printer_id)
        edit_text = PollingEditor().get_favorite_printer_card(printer_info)
        markup.add(types.InlineKeyboardButton(f'ID - {printer_id}',
                                              callback_data=f'download:{double_could}:{printer_cost}')).add(
            PaginatorEditor().cancel)
        await state.set_state(CopyCenterState.download)
    except IndexError:
        edit_text = PollingEditor().get_message('choice_id_not_found')
        markup.add(PaginatorEditor().cancel)
    await state.update_data(chat_id=chat_id, message_id=message_id)
    await dp.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=edit_text, reply_markup=markup)
