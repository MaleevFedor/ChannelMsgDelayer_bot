import sqlalchemy
from .db_session import SqlAlchemyBase


class Message(SqlAlchemyBase):
    __tablename__ = 'messages'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    tg_id = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    sender_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    channel_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.DateTime)
    mediagroup_id = sqlalchemy.Column(sqlalchemy.Integer)
