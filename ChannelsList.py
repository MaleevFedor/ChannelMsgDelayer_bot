from data import db_session
from data.channel_class import Channel
from data.user_class import User


async def create_list_of_channels(user_id):
    db_sess = db_session.create_session()
    db_id = db_sess.query(User).filter(User.tg_id == user_id).first().id
    list_of_channels = db_sess.query(Channel).filter(Channel.user_id == db_id).all()
    db_sess.close()
    result = []
    for i in list_of_channels:
        username = i.ch_username
        if username:
            result.append(f'@{username}')
    return result