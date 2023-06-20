import sqlalchemy
from .db_session import SqlAlchemyBase


class Keyboard(SqlAlchemyBase):
    __tablename__ = 'reply_markup'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    markup_id = sqlalchemy.Column(sqlalchemy.String)
    content = sqlalchemy.Column(sqlalchemy.String)
