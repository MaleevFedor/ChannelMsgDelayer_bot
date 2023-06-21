from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext


async def cancel(message: types.Message, state: FSMContext):
    await message.answer('Действие отменено')
    await state.finish()


def setup(dp: Dispatcher):
    dp.register_message_handler(cancel, state='*', commands='cancel')
