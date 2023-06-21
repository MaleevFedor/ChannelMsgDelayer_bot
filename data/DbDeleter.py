from .message_class import Message
from .reply_markup_class import Keyboard


async def delete_media_group(id, db_sess):
    db_sess.query(Message).filter(Message.mediagroup_id == id).delete()
    db_sess.commit()


async def delete_message(id, db_sess):
    db_sess.query(Message).filter(Message.tg_id == id).delete()
    db_sess.query(Keyboard).filter(id == Keyboard.markup_id).delete()
    db_sess.commit()
