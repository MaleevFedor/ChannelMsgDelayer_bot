import sqlalchemy
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    tg_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, unique=True)
    premium = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

