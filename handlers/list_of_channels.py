from aiogram import types, Dispatcher

from server_functions.ChannelsList import create_list_of_channels


async def get_list_of_channels(message: types.Message):
    list_of_channels = await create_list_of_channels(int(message['from']['id']))
    if len(list_of_channels) == 0:
        await message.answer('Вы ещё не добавили ни один канал')
    else:
        result = 'Ваши добавленные каналы:\n'
        for i in list_of_channels:
            if i:
                result += i + '\n'
        await message.answer(result)


def setup(dp: Dispatcher):
    dp.register_message_handler(get_list_of_channels, commands=['channels_list', 'list_of_channels'])
