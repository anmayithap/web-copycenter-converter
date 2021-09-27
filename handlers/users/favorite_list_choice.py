from aiogram import types
from aiogram.dispatcher import FSMContext

from handlers.users.CopyCenterPolling import PollingEditor, PaginatorEditor
from keyboards.inline.InlinePollingCallBackDatas import method_choice_call_back_data
from loader import dp
from states import CopyCenterState
from utils.db_api.db_editor import PrintersNotInFavoriteList


@dp.callback_query_handler(method_choice_call_back_data.filter(method_name='favorite_list'),
                           state=CopyCenterState.choice_methods)
async def choice_by_favorite_list(call: types.CallbackQuery, state: FSMContext):
    edit_text = ''
    markup = types.InlineKeyboardMarkup()
    user_id = call.message.chat.id
    try:
        printers_id = await PollingEditor().data_base_worker('check_favorite_printer', user_id=user_id)
        for printer_id in printers_id:
            printer_info, double_could, printer_cost = await PollingEditor().create_printer_card(printer_id)
            edit_text += (PollingEditor().get_favorite_printer_card(printer_info) + '\n\n')
            markup.add(types.InlineKeyboardButton(f'ID - {printer_id}',
                                                  callback_data=f'download:{double_could}:{printer_cost}'))
        await state.set_state(CopyCenterState.download)
    except PrintersNotInFavoriteList:
        edit_text += PollingEditor().get_message('favorite_list_is_empty')
    await call.message.edit_text(text=edit_text, reply_markup=markup.add(PaginatorEditor().cancel))
    await PollingEditor().data_base_worker('insert_user', user_id=call.message.chat.id,
                                           user_name=call.message.chat.full_name)
    await state.update_data(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await PollingEditor().add_message_id(state, call.message.message_id)
