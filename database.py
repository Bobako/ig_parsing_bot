import datetime

import sqlalchemy
import sqlalchemy.orm
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, ARRAY, JSON, desc, asc, exc
from sqlalchemy.ext.declarative import declarative_base

from bot_config import *

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    tg_id = Column(Integer, primary_key=True)
    username = Column(String)
    language = Column(String)
    premium_till = Column(DateTime)
    subscriptions_ids = Column(JSON)
    history_ids = Column(JSON)
    orders_uuids = Column(JSON)

    def __init__(self, tg_id: int, username: str, ):
        self.tg_id = tg_id
        self.username = username
        self.language = DEFAULT_LANGUAGE
        self.premium_till = datetime.datetime.now() + datetime.timedelta(seconds=TRIAL_PERIOD_SECONDS)
        self.subscriptions_ids = []
        self.history_ids = []
        self.orders_uuids = []

    def add_premium(self, seconds):
        print(self.premium_till)
        already_premium = self.premium_till - datetime.datetime.now()
        print(already_premium)
        if already_premium < datetime.timedelta(seconds=0):
            already_premium = datetime.timedelta(seconds=0)
        self.premium_till = datetime.datetime.now() + already_premium + datetime.timedelta(seconds=seconds)
        print(self.premium_till)


class IGUser(Base):
    __tablename__ = "ig_users"
    ig_id = Column(BigInteger, primary_key=True)
    username = Column(String)
    last_posts = Column(JSON)
    last_reels = Column(JSON)
    last_stories_urls = Column(ARRAY(String))

    def __init__(self, ig_id, username):
        self.ig_id = ig_id
        self.username = username
        self.last_posts = []
        self.last_reels = []
        self.last_stories_urls = []


class Client(Base):
    __tablename__ = "clients"
    session_id = Column(String, primary_key=True)
    working = Column(Boolean)

    def __init__(self, session_id):
        self.session_id = session_id
        self.working = True


class Handler:
    def __init__(self):
        engine = sqlalchemy.create_engine(f"postgresql+psycopg2://{DB_LOGIN}:{DB_PASSWORD}@{DB_ADDRESS}/{DB_NAME}")
        Base.metadata.create_all(engine)
        self.sessionmaker = sqlalchemy.orm.sessionmaker(bind=engine, expire_on_commit=False)
        self.load_clients()
        print("Database connected")

    def add_user(self, tg_id, username):
        session = self.sessionmaker()
        session.add(User(tg_id, username))
        session.commit()

    def get_user(self, tg_id=None, username=None):
        session = self.sessionmaker()
        user = None
        if tg_id:
            user = session.query(User).filter(User.tg_id == tg_id).one()
        if username:
            user = session.query(User).filter(User.username == username).one()
        session.close()
        return user

    def update_user(self, tg_id, language=None, new_premium_seconds=None, new_subscription_id=None,
                    new_history_id=None, remove_subscription_id=None, new_uuid=None):
        session = self.sessionmaker()
        user = session.query(User).filter(User.tg_id == tg_id).one()
        if language:
            user.language = language
        if new_premium_seconds:
            user.add_premium(new_premium_seconds)
        if new_subscription_id:
            sub_ids = list(map(int, user.subscriptions_ids))
            new_sub_id = int(new_subscription_id)
            if new_sub_id in sub_ids:
                sub_ids.pop(sub_ids.index(new_sub_id))
            sub_ids.append(new_sub_id)
            user.subscriptions_ids = list(sub_ids)
        session.commit()
        if new_history_id:
            history_ids = list(map(int, user.history_ids))
            new_history_id = int(new_history_id)
            if new_history_id in history_ids:
                history_ids.pop(history_ids.index(new_history_id))
            history_ids.append(new_history_id)
            user.history_ids = list(history_ids)
        if remove_subscription_id:
            sub_ids = list(map(int, user.subscriptions_ids))
            remove_sub_id = int(new_subscription_id)
            sub_ids.pop(sub_ids.index(remove_sub_id))
            user.subscriptions_ids = sub_ids
        if new_uuid:
            user.orders_uuids = user.orders_uuids + [new_uuid]
        session.commit()

    def add_ig_user(self, ig_id, username):
        session = self.sessionmaker()
        session.add(IGUser(ig_id, username))
        session.commit()

    def get_ig_user(self, username=None, ig_id=None):
        session = self.sessionmaker()
        if username:
            user = session.query(IGUser).filter(IGUser.username == username).one()
        elif ig_id:
            user = session.query(IGUser).filter(IGUser.ig_id == ig_id).one()
        session.close()
        return user

    def update_ig_user(self, ig_id, username=None, last_posts=None, last_reels=None, new_story_urls=None):
        session = self.sessionmaker()
        user = session.query(IGUser).filter(IGUser.ig_id == ig_id).one()
        if username:
            user.username = username
        if last_posts:
            user.last_posts = last_posts
        if last_reels:
            user.last_reels = last_reels
        if new_story_urls:
            for new_story_url in new_story_urls:
                new_story_url = str(new_story_url)
                user.last_stories_urls = user.last_stories_urls + [new_story_url]
                if len(user.last_stories_urls) > 100:
                    user.last_stories_urls = user.last_stories_urls[1:]
        session.commit()

    def get_premium_users(self):
        session = self.sessionmaker()
        users = session.query(User).filter(User.premium_till > datetime.datetime.now()).all()
        session.close()
        return users

    def get_users(self):
        session = self.sessionmaker()
        users = session.query(User).all()
        session.close()
        return users

    def load_clients(self):
        session = self.sessionmaker()
        with open(IG_ACCS_FILE, "r") as file:
            for session_id in file:
                session_id = session_id.replace("\n", "").replace(" ", "")
                if not session.query(Client).filter(Client.session_id == session_id).first():
                    session.add(Client(session_id))
        session.commit()

    def get_client(self):
        session = self.sessionmaker()
        client = session.query(Client).filter(Client.working == True).first()
        session.close()
        return client

    def mark_client(self, session_id):
        session = self.sessionmaker()
        client = session.query(Client).filter(Client.session_id == session_id).one()
        client.working = False
        session.commit()


class NoMoreAccsAvailable(BaseException):
    pass


if __name__ == '__main__':
    h = Handler()
    h.load_clients()
