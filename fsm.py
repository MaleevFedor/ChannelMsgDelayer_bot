from aiogram.dispatcher.filters.state import State, StatesGroup


class ForwardingMessages(StatesGroup):
    WaitingForMessage = State()


class AddChannels(StatesGroup):
    WaitingForMessage = State()
    WaitingForAdministration = State()
