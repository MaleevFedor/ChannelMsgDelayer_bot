from aiogram.dispatcher.filters.state import State, StatesGroup


class ForwardingMessages(StatesGroup):
    WaitingForMessage = State()
    WaitingForTimeToSchedule = State()
    WaitingForChannelsToBeChosen = State()



class AddChannels(StatesGroup):
    WaitingForMessage = State()
    WaitingForAdministration = State()
