import sqlalchemy
from .db_session import SqlAlchemyBase


class Message(SqlAlchemyBase):
    __tablename__ = 'messages'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    tg_id = sqlalchemy.Column(sqlalchemy.String)
    # file_id for media group, caption for caption
    sender_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    channel_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.DateTime)
    reply_markup = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    mediagroup_id = sqlalchemy.Column(sqlalchemy.Integer)
    type_media = sqlalchemy.Column(sqlalchemy.String)
    is_sent = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    #id_on_post = sqlalchemy.Column(sqlalchemy.String)
