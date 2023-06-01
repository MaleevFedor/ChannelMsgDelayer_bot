import logging
from aiogram import Bot, Dispatcher, executor, types


import config


logging.basicConfig(level=logging.INFO)


bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot)



@dp.message_handler(content_types=[types.ContentType.ANY])
async def echo(message: types.Message):

    if message.text is not None:
        await bot.send_message(-1001945938118, message.text)
    elif message.photo is not None:
        await bot.send_photo(chat_id=-1001945938118, photo=message.photo[-1].file_id,
                             caption=message.caption)
    #await message.answer(message['forward_from_chat']['id'])

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
