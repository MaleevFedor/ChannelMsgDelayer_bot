import logging
from aiogram import Bot, Dispatcher, executor, types


import config


logging.basicConfig(level=logging.INFO)


bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot)

@dp.message_handler()
async def echo(message: types.Message):
    #await bot.send_message()
    await message.answer(message['forward_from_chat']['id'])

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
