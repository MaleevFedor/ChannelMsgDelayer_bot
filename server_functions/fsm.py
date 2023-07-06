from aiogram.dispatcher.filters.state import State, StatesGroup


class ForwardingMessages(StatesGroup):
    WaitingForMessage = State()
    ProceedingCustomization = State()
#    HiddenContinuationText = State()
    URLButton = State()
    HiddenContinuationForAll = State()
    HiddenContinuationForSubs = State()
    WaitingForTimeToSchedule = State()
    WaitingForChannelsToBeChosen = State()


class AddChannels(StatesGroup):
    WaitingForMessage = State()
    WaitingForAdministration = State()
    Nickname = State()


class DealWithPhotos(StatesGroup):
    Next = State()


class ContentPlan(StatesGroup):
    channel_choice = State()
    date_edit = State()
    msg_edit = State()


class TimeZoneChange(StatesGroup):
    Proceed_The_Choice = State()
