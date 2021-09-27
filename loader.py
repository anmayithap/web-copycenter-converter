from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.rethinkdb import RethinkDBStorage
from data import config

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
if config.DEBUG:
    from aiogram.contrib.fsm_storage.memory import MemoryStorage

    storage = MemoryStorage()
else:
    storage = RethinkDBStorage(host=config.RETHINK_HOST,
                               port=config.RETHINK_PORT,
                               db='CopyCenterRDB',
                               table='CopyCenterStates')
dp = Dispatcher(bot, storage=storage)
