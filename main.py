import logging
from aiogram import Dispatcher, executor
import server_functions.Scheduler as Scheduler
from data import db_session
from DispatcherSetup import setup_dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from Bot import bot

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)

db_session.global_init("data.db3")


if __name__ == '__main__':
    setup_dispatcher(dp)
    Scheduler.set_up_scheduler(bot)
    executor.start_polling(dp, skip_updates=False)
