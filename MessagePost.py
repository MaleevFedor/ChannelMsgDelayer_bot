from data.channel_class import Channel
from data.message_class import Message
from data.user_class import User
from aiogram import types, Bot


async def post_media_group(row, db_sess, bot: Bot, channel_id=None, reply_markup=None):
    media_group = types.MediaGroup()
    media_group_parts = db_sess.query(Message).filter(Message.mediagroup_id == row, Message.type_media != 'caption').all()
    caption = db_sess.query(Message).filter(Message.mediagroup_id == row, Message.type_media == 'caption').first().tg_id
    caption = str(caption)
    for i in media_group_parts:
        media_group.attach({"media": i.tg_id, "type": i.type_media, "caption": caption})
        caption = None
    if not channel_id:
        channel_id = db_sess.query(Channel).filter(media_group_parts[0].channel_id == Channel.id).first().tg_id
    await bot.send_media_group(media=media_group, chat_id=channel_id)


async def post_message(row, db_sess, bot: Bot, channel_id=None, reply_markup=None):
    sender_id = db_sess.query(User).filter(row.sender_id == User.id).first().tg_id
    if not channel_id:
        channel_id = db_sess.query(Channel).filter(row.channel_id == Channel.id).first().tg_id
    await bot.copy_message(chat_id=channel_id, from_chat_id=sender_id, message_id=row.tg_id, reply_markup=reply_markup)
