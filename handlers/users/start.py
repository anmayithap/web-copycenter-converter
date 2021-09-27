import math

from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
import os

from aiogram.utils.exceptions import MessageToDeleteNotFound

from settings import MEDIA_DIR
from utils.misc import rate_limit
from aiogram.dispatcher.storage import FSMContext

from loader import dp
from .CopyCenterPolling import PollingEditor
from utils.convert_api.file_handler import clear_data_base


class StartEditor(PollingEditor):
    PollingEditor.EMOJI_LIST.update({'hello': '👋'})

    @classmethod
    def get_message(cls, state, **kwargs):
        user_full_name = kwargs['user_full_name']
        message_list = {
            '/start': {
                'message': f'Добро пожаловать, {user_full_name} {cls.EMOJI_LIST["hello"]}\n'
                           f'Я помогу тебе с распечаткой твоих файлов {cls.EMOJI_LIST["document"]}.\n'
                           f'Нажми на кнопку для начала работы, '
                           f'или напиши /start_copy_center {cls.EMOJI_LIST["great"]}.',
                'sticker': 'welcome.tgs'
            }
        }
        return message_list[state]


@rate_limit(2)
@dp.message_handler(CommandStart(), state='*')
async def bot_start(message: types.Message, state: FSMContext):
    await clear_data_base(message.from_user.id)
    data = await state.get_data()
    try:
        for message_id in data['another_messages_id']:
            try:
                await dp.bot.delete_message(chat_id=message.chat.id, message_id=message_id)
            except MessageToDeleteNotFound:
                continue
    except KeyError:
        await message.delete()
    await state.finish()
    message_context = StartEditor.get_message(message.text, user_full_name=message.from_user.full_name)
    sticker = open(os.path.join(MEDIA_DIR, message_context['sticker']), 'rb')
    await dp.bot.send_sticker(chat_id=message.from_user.id, sticker=sticker)
    await dp.bot.send_message(chat_id=message.from_user.id, text=message_context['message'])
