from aiogram import types, Dispatcher


async def commands_list(message: types.Message):
    await message.answer("/add_channel - добавить канал\n/forward - запланировать пересылку сообщения\n"
                         "/content_plan - просмотреть список запланированных сообщений\n"
                         "/cancel - отменить любое действие")


def setup(dp: Dispatcher):
    dp.register_message_handler(commands_list, commands='help')
