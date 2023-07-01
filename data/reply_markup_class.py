import sqlalchemy
from .db_session import SqlAlchemyBase


class Keyboard(SqlAlchemyBase):
    __tablename__ = 'reply_markup'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    markup_id = sqlalchemy.Column(sqlalchemy.String)
    content = sqlalchemy.Column(sqlalchemy.String)
    content_text = sqlalchemy.Column(sqlalchemy.String)
    content_for_all = sqlalchemy.Column(sqlalchemy.String)
    content_for_subs = sqlalchemy.Column(sqlalchemy.String)