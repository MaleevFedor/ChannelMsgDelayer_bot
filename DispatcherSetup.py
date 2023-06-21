from aiogram import Dispatcher
from middlewares import AlbumHandler as ah
from handlers import registration, cancellation, timezone, help, adding_channel, list_of_channels, content_plan, \
    forwarding_message


def setup_dispatcher(dp: Dispatcher):
    dp.middleware.setup(ah.AlbumMiddleware())
    # add all middlewares

    registration.setup(dp)
    cancellation.setup(dp)
    timezone.setup(dp)
    help.setup(dp)
    adding_channel.setup(dp)
    list_of_channels.setup(dp)
    content_plan.setup(dp)
    forwarding_message.setup(dp)
    # add all commands
