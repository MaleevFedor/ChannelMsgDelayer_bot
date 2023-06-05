import datetime
import asyncio
from sqlalchemy.orm.session import Session
from data.message_class import Message


async def delay(msg_id, seconds, post_func):
    await asyncio.sleep(seconds)
    await post_func(msg_id)


async def set_today_schedule(db_sess: Session, post_func):
    today_messages = db_sess.query(Message).filter(datetime.date.today() == Message.date).all()
    # TODO understand how to get only the date
    for i in today_messages:
        msg_id = i['tg_id']
        seconds = i['date'] - datetime.datetime.now()
        await delay(msg_id, seconds.seconds, post_func)
    db_sess.close()
