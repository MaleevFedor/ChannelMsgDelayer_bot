from aiogram.dispatcher.filters.state import State, StatesGroup


class ForwardingMessages(StatesGroup):
    WaitingForMessage = State()
  #  DealWithPhotos = State()
    NextFile = State()
    WaitingForTimeToSchedule = State()
    WaitingForChannelsToBeChosen = State()


class AddChannels(StatesGroup):
    WaitingForMessage = State()
    WaitingForAdministration = State()


class DealWithPhotos(StatesGroup):
    Next = State()


class ContentPlan(StatesGroup):
    channel_choice = State()
    date_edit = State()
    msg_edit = State()
