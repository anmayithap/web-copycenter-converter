from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandHelp

from loader import dp
from utils.misc import rate_limit
from aiogram.dispatcher.storage import FSMContext
from aiogram.utils.exceptions import MessageToDeleteNotFound
from utils.convert_api.file_handler import clear_data_base


@rate_limit(5, 'help')
@dp.message_handler(CommandHelp(), state='*')
async def bot_help(message: types.Message, state: FSMContext):
    await clear_data_base(user_id=message.from_user.id)
    await state.finish()
    for number in range(100000):
        try:
            await dp.bot.delete_message(message.chat.id, message.message_id - number)
        except MessageToDeleteNotFound:
            break
    text = [
        'Список команд: ',
        '/start - Начать диалог',
        '/help - Получить справку',
        '/start_copy_center - Начать заполнение формы'
    ]
    await message.answer('\n'.join(text))
