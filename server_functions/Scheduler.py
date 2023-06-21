import datetime
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from data.DbDeleter import delete_media_group, delete_message
from .MessagePost import post_media_group, post_message
from data import db_session
from data.message_class import Message


async def check_and_post(bot: Bot):
    db_sess = db_session.create_session()
    media_groups_id = set(
        [i.mediagroup_id for i in db_sess.query(Message).filter(Message.date <= datetime.datetime.now(),
                                                                Message.mediagroup_id != None).all()])
    not_media_groups = db_sess.query(Message).filter(Message.date <= datetime.datetime.now(),
                                                     Message.mediagroup_id == None).all()
    for row in media_groups_id:
        await post_media_group(row, db_sess, bot)
        await delete_media_group(row, db_sess)
    for row in not_media_groups:
        await post_message(row, db_sess, bot)
        await delete_message(row.tg_id, db_sess)
    db_sess.close()


def set_up_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_and_post, trigger='interval', seconds=5, args=(bot,))
    scheduler.start()
