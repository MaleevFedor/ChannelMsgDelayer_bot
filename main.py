import logging
from aiogram import Bot, Dispatcher, executor, types


import config


logging.basicConfig(level=logging.INFO)


bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot)



@dp.message_handler(content_types=[types.ContentType.ANY])
async def echo(message: types.Message):
    await message.answer(message['forward_from_chat']['id'])

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
