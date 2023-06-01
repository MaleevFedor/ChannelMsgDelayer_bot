import sqlalchemy
from .db_session import SqlAlchemyBase


class Channel(SqlAlchemyBase):
    __tablename__ = 'channels'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    tg_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, unique=True)