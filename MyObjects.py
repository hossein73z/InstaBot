from sqlalchemy import create_engine, Column, Integer, String, JSON, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

engine = create_engine("sqlite:///database.db")
factory = sessionmaker(bind=engine)

Base = declarative_base()
Base.get_table_name = lambda self: self.__tablename__


class Person(Base):
    __tablename__ = "persons"

    id = Column(name='id', type_=Integer, primary_key=True)
    chat_id = Column(name="chat_id", type_=Integer)
    first_name = Column(name="first_name", type_=String)
    last_name = Column(name="last_name", type_=String)
    username = Column(name="username", type_=String)
    session = Column(name='session', type_=JSON)
    insta_username = Column(name='insta_username', type_=String)
    progress = Column(name="progress", type_=JSON)
    admin = Column(name="admin", type_=Integer)
    btn_id = Column(name="btn_id", type_=Integer)
    sp_btn_id = Column(name="sp_btn_id", type_=Integer)

    def __int__(self,
                chat_id: int,
                first_name: str,
                admin: int = 0,
                id: int | None = None,
                last_name: str | None = None,
                username: str | None = None,
                session: dict | None = None,
                progress: dict | None = None,
                btn_id: int = 0,
                sp_btn_id: int | None = None):
        self.id = id
        self.chat_id = chat_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.session = session
        self.progress = progress
        self.admin = admin
        self.btn_id = btn_id
        self.sp_btn_id = sp_btn_id


class Setting(Base):
    __tablename__ = "settings"

    id = Column(name="id", type_=Integer, primary_key=True)
    name = Column(name="name", type_=Integer)
    value = Column(name="value", type_=String)

    def __init__(self,
                 id: int,
                 name: str,
                 value: str = None):
        self.id = id
        self.name = name
        if value:
            self.value = value
