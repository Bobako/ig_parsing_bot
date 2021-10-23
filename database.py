import datetime

import sqlalchemy
import sqlalchemy.orm
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ARRAY, JSON, desc, asc
from sqlalchemy.ext.declarative import declarative_base

from bot_config import *

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    tg_id = Column(Integer, primary_key=True)
    username = Column(String)
    language = Column(String)
    premium_till = Column(DateTime)
    subscriptions_ids = Column(ARRAY)
    history_ids = Column(ARRAY)

    def __init__(self, tg_id: int, username: str, ):
        self.tg_id = tg_id
        self.username = username
        self.language = DEFAULT_LANGUAGE
        self.premium_till = datetime.datetime.now() + datetime.timedelta(seconds=TRIAL_PERIOD_SECONDS)
        self.subscriptions_ids = []
        self.history_ids = []

    def add_premium(self, seconds):
        already_premium = self.premium_till - datetime.datetime.now()
        if already_premium < datetime.timedelta(seconds=0):
            already_premium = datetime.timedelta(seconds=0)
        self.premium_till = datetime.datetime.now() + already_premium + datetime.timedelta(seconds)


class IGUser(Base):
    __tablename__ = "ig_users"
    ig_id = Column(Integer, primary_key=True)
    username = Column(String)
    last_posts = Column(JSON)
    last_reels = Column(JSON)
    last_stories_urls = Column(ARRAY)

    def __init__(self, ig_id, username):
        self.ig_id = ig_id
        self.username = username
        self.last_posts = {}
        self.last_stories = {}
        self.last_stories_urls = []


class Handler:
    def __init__(self):
        engine = sqlalchemy.create_engine(f"postgresql+psycopg2://{DB_LOGIN}:{DB_PASSWORD}@{DB_ADDRESS}/{DB_NAME}")
        Base.metadata.create_all(engine)
        self.sessionmaker = sqlalchemy.orm.sessionmaker(bind=engine, expire_on_commit=False)

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

    def update_user(self, tg_id, language=None, new_premium_seconds=None, new_subscription=None, new_history_id=None):
        session = self.sessionmaker()
        user = session.query(User).filter(User.tg_id == tg_id).one()
        if language:
            user.language = language
        if new_premium_seconds:
            user.add_premium(new_premium_seconds)
        if new_subscription:
            if new_subscription not in user.subscriptions_ids:
                user.subscriptions_ids.append(new_subscription)
        if new_history_id:
            if new_history_id not in user.history_ids:
                user.new_history_id.append(new_history_id)
        session.commit()

    def add_ig_user(self, ig_id, username):
        session = self.sessionmaker()
        session.add(IGUser(ig_id, username))
        session.commit()

    def get_ig_user(self, username):
        session = self.sessionmaker()
        user = session.query(IGUser).filter(IGUser.username == username).one()
        session.close()
        return user

    def update_ig_user(self, ig_id, username=None, last_posts=None, last_reels=None, new_story_url=None):
        session = self.sessionmaker()
        user = session.query(IGUser).filter(IGUser.ig_id == ig_id).one()
        if username:
            user.username = username
        if last_posts:
            user.last_posts = last_posts
        if last_reels:
            user.last_reels = last_reels
        if new_story_url:
            user.last_stories_urls.append(new_story_url)
            if len(user.last_stories_urls) > 100:
                user.last_stories_urls = user.last_stories_urls[1:]
        session.commit()


if __name__ == '__main__':
    h = Handler()
