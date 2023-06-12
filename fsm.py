from aiogram.dispatcher.filters.state import State, StatesGroup


class ForwardingMessages(StatesGroup):
    WaitingForMessage = State()
  #  DealWithPhotos = State()
    NextPhoto = State()
    WaitingForTimeToSchedule = State()
    WaitingForChannelsToBeChosen = State()



class AddChannels(StatesGroup):
    WaitingForMessage = State()
    WaitingForAdministration = State()

class DealWithPhotos(StatesGroup):
    Next = State()