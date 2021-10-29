import datetime
import json
import math
import time
import urllib.request
from threading import Thread
import uuid

import sqlalchemy.exc
import telebot
from telebot import types
from telebot.types import ReplyKeyboardRemove as RemoveMarkup
from bottle import run, request, post

import database
from bot_config import *
from ig_parser import Parser, IGRedirectError, NoSuchUserError, NoMaterialsFoundError

h = database.Handler()

bot = telebot.TeleBot(BOT_TOKEN)
parser = Parser(IG_LOGIN, IG_PASSWORD, proxy=PROXY_ADDR)

MATERIALS = []


# start branch
@bot.message_handler(commands=["start", "language"])
def start(message):
    tg_id = message.from_user.id
    username = message.from_user.username
    try:
        h.add_user(tg_id, username)
    except sqlalchemy.exc.IntegrityError:
        user = h.get_user(tg_id)
        bot.send_message(tg_id, MSGS[user.language]["START_MSG"], reply_markup=get_languages_keyboard(False))
    else:
        user = h.get_user(tg_id)
        bot.send_message(tg_id, MSGS[user.language]["START_MSG"], reply_markup=get_languages_keyboard())


def register_referal(message):
    if message.text not in [lang["skip"] for lang in list(MSGS.values())]:
        username = message.text.replace("@", "")
        try:
            tg_id = h.get_user(username=username).tg_id
        except sqlalchemy.exc.NoResultFound:
            pass
        else:
            h.update_user(tg_id, new_premium_seconds=REFERER_PERIOD_SECONDS)
        bot.send_message(message.from_user.id, MSGS[h.get_user(message.from_user.id).language]["thanks"],
                         reply_markup=RemoveMarkup())
    help_(message)


@bot.message_handler(commands=["help"])
def help_(message):
    sender = message.chat.id

    user = h.get_user(tg_id=sender)
    bot.send_message(sender, MSGS[user.language]["HELP_MSG"].format(user.premium_till.strftime("%Y.%m.%d %H:%M")),
                     reply_markup=RemoveMarkup())


# methods branch
@bot.message_handler(commands=["stories", "posts", "reels", "highlights", "subscribe", "unsubscribe"])
def input_username(message):
    sender = message.from_user.id
    user = h.get_user(sender)
    lang = user.language
    if user.premium_till < datetime.datetime.now():
        bot.send_message(sender, MSGS[lang]["PREMIUM_EXPIRED_MSG"])
        return


    bot.send_message(sender, MSGS[lang]["INPUT_USERNAME_MSG"], reply_markup=get_history_keyboard(h.get_user(sender)))
    if message.text == "/stories":
        bot.register_next_step_handler(message, stories)

    elif message.text == "/posts":
        bot.register_next_step_handler(message, posts)

    elif message.text == "/reels":
        bot.register_next_step_handler(message, reels)

    elif message.text == "/highlights":
        bot.register_next_step_handler(message, highlights)

    elif message.text == "/subscribe":
        bot.register_next_step_handler(message, subscribe)

    elif message.text == "/unsubscribe":
        bot.register_next_step_handler(message, unsubscribe)


@bot.message_handler(commands=["support"])
def support(message):
    user = h.get_user(message.from_user.id)
    bot.send_message(user.tg_id, MSGS[user.language]["SUPPORT_MSG"])


@bot.message_handler(commands=["history"])
def history(message):
    user = h.get_user(message.from_user.id)
    history = user.history_ids
    if history:
        ig_users = [h.get_ig_user(ig_id=id_).username for id_ in history]
        history = "\n ".join(ig_users)
        bot.send_message(user.tg_id, history)
    else:
        bot.send_message(user.tg_id, MSGS[user.language]["NoHistoryError"])


def subscribe(message):
    user = h.get_user(message.from_user.id)
    username = message.text
    if not (uid := get_uid(username, user)):
        return
    h.update_user(user.tg_id, new_subscription_id=uid)
    bot.send_message(user.tg_id, MSGS[user.language]["SUBSCRIPTION_MSG"].format(username))
    check_for_updates(h.get_ig_user(ig_id=uid), True)


def unsubscribe(message):
    user = h.get_user(message.from_user.id)
    username = message.text
    if not (uid := get_uid(username, user)):
        return
    h.update_user(user.tg_id, remove_subscription_id=uid)
    bot.send_message(user.tg_id, MSGS[user.lang]["UNSUBSCRIPTION_MSG"].format(username))


@bot.message_handler(commands=["premium"])
def premium(message):
    user = h.get_user(message.from_user.id)
    bot.send_message(user.tg_id, MSGS[user.language]["PREMIUM_MSG"], reply_markup=get_premium_keyboard(user))


def stories(message):
    user = h.get_user(message.from_user.id)
    username = message.text
    if not (uid := get_uid(username, user)):
        return
    wait_message = bot.send_message(user.tg_id, text="⏳", reply_markup=RemoveMarkup())
    urls = safe_get(user, parser.get_stories_by_uid, uid)
    if urls:
        paginator(user, urls, page_type="stories")
    bot.delete_message(user.tg_id, wait_message.id)


def posts(message):
    user = h.get_user(message.from_user.id)
    username = message.text
    wait_message = bot.send_message(user.tg_id, text="⏳", reply_markup=RemoveMarkup())
    posts, uid = safe_get(user, parser.get_posts, username, 0, POSTS_LIMIT)
    if posts:
        store_uid(uid, username, user)
        paginator(user, posts, page_type="posts")
    bot.delete_message(user.tg_id, wait_message.id)


def reels(message):
    user = h.get_user(message.from_user.id)
    username = message.text
    if not (uid := get_uid(username, user)):
        return
    wait_message = bot.send_message(user.tg_id, text="⏳", reply_markup=RemoveMarkup())
    reels_ = safe_get(user, parser.get_reels_by_uid, uid, 0, POSTS_LIMIT)
    if reels_:
        paginator(user, reels_, page_type="reels")
    bot.delete_message(user.tg_id, wait_message.id)


def highlights(message):
    user = h.get_user(message.from_user.id)
    username = message.text
    if not (uid := get_uid(username, user)):
        return
    wait_message = bot.send_message(user.tg_id, text="⏳", reply_markup=RemoveMarkup())
    hls = safe_get(user, parser.get_highlights_list_by_uid, uid)
    if hls:
        paginator(user, hls, page_type="highlights")
    bot.delete_message(user.tg_id, wait_message.id)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    sender = call.from_user.id
    data = json.loads(call.data)
    if "lang" in data:
        lang = data["lang"]
        h.update_user(sender, language=lang)
        message = bot.send_message(sender, MSGS[lang]["lang_updated"])
        bot.answer_callback_query(call.id)
        if data["first_time"]:
            bot.send_message(sender, MSGS[lang]["REF_MSG"], reply_markup=get_ref_keyboard(lang))
            bot.register_next_step_handler(message, register_referal)
        else:
            help_(message)
    if "paginator" in data:
        if data["paginator"] == "placeholder":
            return
        user = h.get_user(call.from_user.id)
        data = json.loads(call.data)
        page = data["page"]
        materials = MATERIALS[data["mid"]]
        pag_msg = call.message
        mid = data["mid"]
        if data["paginator"] == "next":
            page += 1
            paginator(user, materials.materials, materials, pag_msg, materials.material_type, page, mid)
        elif data["paginator"] == "prev":
            page -= 1
            paginator(user, materials.materials, materials, pag_msg, materials.material_type, page, mid)
        elif data["paginator"] == "expand":
            expand(user, pag_msg, page, materials, mid)
        elif data["paginator"] == "hide":
            expand(user, pag_msg, page, materials, mid, expanded=False)
        elif data["paginator"] == "about":
            about(user, mid, page)

    if "premium" in data:
        order_uuid = str(uuid.uuid4())
        price = data["price"]
        url = f"{PAYMENT_DOMAIN}{PAYMENT_PATH}?order={order_uuid}&sum={price}"
        bot.delete_message(sender, call.message.id)
        bot.send_message(sender, url)
        h.update_user(sender, new_uuid=order_uuid)

    bot.answer_callback_query(call.id)


def about(user, mid, post_id):
    material: Material = MATERIALS[mid]
    post = material.materials[post_id]
    media = []
    if material.material_type == "posts":
        filenames = download_sources(post["urls"][:10])
        for filename in filenames:
            if filename[-3:] == "mp4":
                media.append(types.InputMediaVideo(open(filename, "rb")))
            elif filename[-3:] == "jpg":
                media.append(types.InputMediaPhoto(open(filename, "rb")))
        caption = MSGS[user.language]["post_info"].format(format_timestamp(post["timestamp"]),
                                                          post["likes"], post["comments"])
        caption += "\n" + post["caption"]
        if material.about_media_message_ids:
            bot.delete_message(user.tg_id, material.about_caption_message_id)
            for id_ in material.about_media_message_ids:
                bot.delete_message(user.tg_id, id_)
        wait_message = bot.send_message(user.tg_id, text="⏳", reply_markup=RemoveMarkup())
        about_media_messages = bot.send_media_group(user.tg_id, media)
        about_caption_message = bot.send_message(user.tg_id, caption)
        bot.delete_message(user.tg_id, wait_message.id)
        material.about_media_message_ids = [m.id for m in about_media_messages]
        material.about_caption_message_id = about_caption_message.id

    elif material.material_type == "highlights":
        if material.about_media_message_ids:
            if material.about_caption_message_id:
                bot.delete_message(user.tg_id, material.about_caption_message_id)
            for id_ in material.about_media_message_ids:
                bot.delete_message(user.tg_id, id_)
        wait_message = bot.send_message(user.tg_id, text="⏳", reply_markup=RemoveMarkup())
        highlight = material.materials[post_id]
        hl_id = highlight["id"]
        urls = safe_get(user, parser.get_highlight_stories, hl_id)

        about_media_messages_ids, about_caption_message_id = paginator(user, urls, page_type="stories")
        material.about_caption_message_id = about_caption_message_id
        material.about_media_message_ids = about_media_messages_ids

        bot.delete_message(user.tg_id, wait_message.id)


def expand(user, pag_msg, page, materials, mid, expanded=True):
    pages = math.ceil(len(materials.materials) / ELEMENTS_PER_PAGE)
    pag_keys = get_paginator_keyboard(user, mid, page != 1, page < pages, True, page, expanded)
    bot.edit_message_reply_markup(user.tg_id, pag_msg.id, reply_markup=pag_keys)


def paginator(user, raw_materials=None, materials=None, pag_msg=None, page_type="", page=1, mid=0):
    end = page * ELEMENTS_PER_PAGE
    start = end - ELEMENTS_PER_PAGE
    if page_type == "reels":
        end = page * REELS_PER_PAGE
        start = end - REELS_PER_PAGE
    pages = math.ceil(len(raw_materials) / ELEMENTS_PER_PAGE)
    media = []
    caption = ""
    if page_type == "stories":
        for raw_material in raw_materials[start:end]:
            filename = download_sources([raw_material])[0]
            if filename[-3:] == "mp4":
                media.append(types.InputMediaVideo(open(filename, "rb")))
            elif filename[-3:] == "jpg":
                media.append(types.InputMediaPhoto(open(filename, "rb")))
    elif page_type == "posts":
        for i, raw_material in enumerate(raw_materials[start:end]):
            filename = download_sources([raw_material["urls"][0]])[0]
            if filename[-3:] == "mp4":
                media.append(types.InputMediaVideo(open(filename, "rb")))
            elif filename[-3:] == "jpg":
                media.append(types.InputMediaPhoto(open(filename, "rb")))
            caption += f"{i + 1} ({format_timestamp(raw_material['timestamp'])})" \
                       f" {raw_material['caption'][:MAX_SYMBOLS_PREVIEW]}" \
                       f"{('...' if len(raw_material['caption']) > MAX_SYMBOLS_PREVIEW else '')}\n\n"

    elif page_type == "reels":
        for i, raw_material in enumerate(raw_materials[start:end]):
            filename = download_sources([raw_material["url"]])[0]
            if filename[-3:] == "mp4":
                media.append(types.InputMediaVideo(open(filename, "rb")))
            elif filename[-3:] == "jpg":
                media.append(types.InputMediaPhoto(open(filename, "rb")))
            caption += f"{i + 1}." \
                       f" {MSGS[user.language]['post_info'].format(format_timestamp(raw_material['timestamp']), raw_material['likes'], raw_material['comments'])}\n\n"

    elif page_type == "highlights":
        for i, raw_material in enumerate(raw_materials[start:end]):
            filename = download_sources([raw_material["thumbnail"]])[0]
            if filename[-3:] == "mp4":
                media.append(types.InputMediaVideo(open(filename, "rb")))
            elif filename[-3:] == "jpg":
                media.append(types.InputMediaPhoto(open(filename, "rb")))
            caption += f"{i + 1}. {raw_material['title']}\n"
    if (pages != 1) and page == pages:
        for _ in range(end - start - len(media)):
            media.append(types.InputMediaPhoto(open(PLACEHOLDER_IMAGE_PATH, "rb")))

    if not caption:
        caption = MSGS[user.language]["paginator"].format(page, pages)
    if not pag_msg:
        media_messages = bot.send_media_group(user.tg_id, media)
        media_messages_ids = [media_message.message_id for media_message in media_messages]
        if not (page_type == "stories" and pages == 1):
            mid = Material(page_type, raw_materials, media_messages_ids).i
            pag_keys = get_paginator_keyboard(user, mid, page != 1, page < pages, page_type in ["posts", "highlights"],
                                              page)
            pag_msg = bot.send_message(user.tg_id, caption, reply_markup=pag_keys)
            return media_messages_ids, pag_msg.id
        return media_messages_ids, None
    else:
        for media_id, media in zip(materials.media_message_ids, media):
            bot.edit_message_media(media, user.tg_id, media_id)
        pag_keys = get_paginator_keyboard(user, mid, page != 1, page < pages, page_type in ["posts", "highlights"],
                                          page)
        bot.edit_message_text(caption, user.tg_id, pag_msg.id, reply_markup=pag_keys)
        return materials.media_message_ids, pag_msg.id


# keyboards
def get_ref_keyboard(lang):
    keyboard = types.ReplyKeyboardMarkup()
    key_skip = types.KeyboardButton(MSGS[lang]["skip"])
    keyboard.add(key_skip)
    return keyboard


def get_languages_keyboard(first_time=True):
    keyboard = types.InlineKeyboardMarkup()
    langs = list(MSGS.keys())
    icons = [lang["icon"] for lang in list(MSGS.values())]
    btns = []
    for lang, icon in zip(langs, icons):
        btns.append(types.InlineKeyboardButton(text=icon, callback_data=json.dumps({"lang": lang,
                                                                                    "first_time": first_time})))
    keyboard.row(*btns)
    return keyboard


def get_paginator_keyboard(user, mid, prev=False, next=False, expandable=False, page=1, expanded=False):
    tg_id = user.tg_id
    lang = user.language
    keyboard = types.InlineKeyboardMarkup()
    btns = []

    if prev:
        btns.append(types.InlineKeyboardButton(text="⬅", callback_data=json.dumps({"paginator": "prev",
                                                                                   "mid": mid,
                                                                                   "page": page})))
    else:
        btns.append(types.InlineKeyboardButton(text=" ", callback_data=json.dumps({"paginator": "placeholder"})))

    if expandable:
        text = MSGS[lang]["hide"] if expanded else MSGS[lang]["choice"]
        func = 'hide' if expanded else 'expand'
        btns.append(types.InlineKeyboardButton(text=text, callback_data=json.dumps({"paginator": func,
                                                                                    "mid": mid,
                                                                                    "page": page})))
    else:
        btns.append(types.InlineKeyboardButton(text=" ", callback_data=json.dumps({"paginator": "placeholder"})))

    if next:
        btns.append(types.InlineKeyboardButton(text="➡", callback_data=json.dumps({"paginator": "next",
                                                                                   "mid": mid,
                                                                                   "page": page})))
    else:
        btns.append(types.InlineKeyboardButton(text=" ", callback_data=json.dumps({"paginator": "placeholder"})))

    keyboard.row(*btns)
    if expanded:
        l = len(MATERIALS[mid].materials)
        pages = math.ceil(l / ELEMENTS_PER_PAGE)
        if page == pages:
            materials_count = l % ELEMENTS_PER_PAGE
        else:
            materials_count = ELEMENTS_PER_PAGE
        btns = []
        start_number = (page - 1) * ELEMENTS_PER_PAGE
        for i in range(ELEMENTS_PER_PAGE):
            if i < materials_count:
                btns.append(
                    types.InlineKeyboardButton(text=f"{i + 1}", callback_data=json.dumps({"paginator": "about",
                                                                                          "mid": mid,
                                                                                          "page": start_number + i})))
            else:
                btns.append(
                    types.InlineKeyboardButton(text=" ", callback_data=json.dumps({"paginator": "placeholder"})))
            if (i + 1) % 3 == 0:
                keyboard.row(*btns)
                btns = []
    return keyboard


def get_history_keyboard(user):
    if user.history_ids:
        keyboard = types.ReplyKeyboardMarkup()
        for ig_id in user.history_ids[-1:-10:-1]:
            keyboard.row(types.KeyboardButton(h.get_ig_user(ig_id=ig_id).username))
        return keyboard


def get_premium_keyboard(user):
    keyboard = types.InlineKeyboardMarkup()
    btns = []
    for dict_ in PAYED_PERIOD_SECONDS_PRICES:
        price = dict_["price"]
        period = dict_["period"]
        period_days = int(period / 3600 / 24)
        btns.append(types.InlineKeyboardButton(MSGS[user.language]["PREMIUM_OPTION"].format(period_days, price),
                                               callback_data=json.dumps({"premium": "",
                                                                         "price": price})))
    keyboard.row(*btns)
    return keyboard


# other
def safe_get(user, method, *args):
    try:
        result = method(*args)
    except IGRedirectError:
        if user:
            bot.send_message(user.tg_id, MSGS[user.language]["IGRedirectError"])
    except NoSuchUserError:
        if user:
            bot.send_message(user.tg_id, MSGS[user.language]["NoSuchUserError"])
    except NoMaterialsFoundError:
        if user:
            bot.send_message(user.tg_id, MSGS[user.language]["NoMaterialsFoundError"])
    else:
        return result


def get_uid(username, user):
    if "instagram.com/" in username:
        username = username[username.find("instagram.com/")+14:]
        if username[-1] == "/":
            username = username[:-1]
    uid = 0
    try:
        uid = h.get_ig_user(username).ig_id
    except sqlalchemy.exc.NoResultFound:
        uid = safe_get(user, parser.get_user_id, username)
        if not uid:
            return
        h.add_ig_user(uid, username)
    finally:
        h.update_user(user.tg_id, new_history_id=uid)
        return uid


def store_uid(uid, username, user):
    try:
        h.add_ig_user(uid, username)
    except sqlalchemy.exc.IntegrityError:
        pass
    h.update_user(user.tg_id, new_history_id=uid)


def download_sources(urls):
    filenames = []
    for url in urls:
        last_slash = len(url) - url[-1:0:-1].find("/")
        filename = SAVE_DIRECTORY + url[last_slash:url.find("?")]
        filenames.append(filename)
        try:
            with open(filename, "rb"):
                pass
        except FileNotFoundError:
            urllib.request.urlretrieve(url, filename)
    return filenames


def format_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime("%Y.%m.%d %H:%M")


class Material:
    material_type = ""
    materials = []
    media_message_ids = []
    about_media_message_ids = None
    about_caption_message_id = None

    def __init__(self, material_type, materials, media_message_ids):
        self.material_type = material_type
        self.materials = materials
        self.media_message_ids = media_message_ids
        global MATERIALS
        MATERIALS.append(self)
        self.i = len(MATERIALS) - 1


def check_for_updates_loop():
    while True:
        users = h.get_premium_users()
        l = len(users)
        for user in users:
            for ig_id in user.subscriptions_ids:
                ig_user = h.get_ig_user(ig_id=ig_id)
                new_stories, new_posts, new_reels = check_for_updates(ig_user)
                if new_stories or new_posts or new_reels:
                    bot.send_message(user.tg_id,
                                     MSGS[user.language]["SUBSCRIPTION_UPDATE_MSG"].format(ig_user.username))
                    if new_stories:
                        paginator(user, new_stories, page_type="stories")
                    if new_posts:
                        paginator(user, new_posts, page_type="posts")
                    if new_reels:
                        paginator(user, new_reels, page_type="reels")
            time.sleep(SUBSCRIPTION_CHECK_PERIOD / l)


def check_for_updates_safe_loop():
    print("Subscription loop is running")
    while True:
        try:
            check_for_updates_loop()
        except Exception as ex:
            print(ex)


def check_for_updates(ig_user, first_time=False):
    if first_time and (ig_user.last_posts or ig_user.last_reels or ig_user.last_stories_urls):
        return
    username = ig_user.username
    uid = ig_user.ig_id
    stories_ = safe_get(None, parser.get_stories_by_uid, uid)
    posts_, _ = safe_get(None, parser.get_posts, username, 0, 11)
    reels_ = safe_get(None, parser.get_reels_by_uid, uid, 0, 11)

    if not first_time:
        new_stories = []
        new_posts = []
        new_reels = []
        if stories_:
            for story in stories_:
                if not in_id(story, ig_user.last_stories_urls):
                    new_stories.append(story)
        if posts_:
            for post in posts_:
                if not in_id(post, ig_user.last_posts):
                    new_posts.append(post)
        if reels_:
            for reel in reels_:
                if not in_id(reel, ig_user.last_reels):
                    new_reels.append(reel)

    if stories_:
        h.update_ig_user(uid, new_story_urls=stories_)
    if posts_:
        h.update_ig_user(uid, last_posts=posts_)
    if reels_:
        h.update_ig_user(uid, last_reels=reels_)

    if not first_time:
        return new_stories, new_posts, new_reels


@post(BOT_PAYMENT_ROUTE)
def await_payment():
    postdata = request.json
    order_uuid = postdata["orderUuid"]
    sum = postdata["sum"]
    status = postdata["status"]
    users = h.get_users()
    user_ = None
    for user in users:
        if order_uuid in user.orders_uuids:
            user_ = user
            break
    if status == "success":
        period_ = None
        price_ = None
        for dict_ in PAYED_PERIOD_SECONDS_PRICES:
            period = dict_["period"]
            price = dict_["price"]
            if float(price) == float(sum):
                period_ = period
                price_ = price
                break
        h.update_user(user_.tg_id, new_premium_seconds=period_)
        user_ = h.get_user(user_.tg_id)
        bot.send_message(user_.tg_id,
                         MSGS[user_.language]["PREMIUM_ADDED"].format(user_.premium_till.strftime("%Y.%m.%d %H:%M")))
    else:
        bot.send_message(user_.tg_id,
                         MSGS[user_.language]["PAYMENT_ERROR"])


def run_backend():
    print("Backend is running")
    while True:
        try:
            run(host=BOT_DOMAIN, port=BOT_PORT, debug=False)
        except Exception as ex:
            print(ex)


def in_id(material, materials):
    if type(material) != str:
        material = int(material["id"])
        materials = [int(m["id"]) for m in materials]
    return material in materials


if __name__ == '__main__':
    updates_checker = Thread(target=check_for_updates_safe_loop)
    updates_checker.start()
    backend = Thread(target=run_backend)
    backend.start()
    print("Bot is running")
    while True:
        try:
            bot.infinity_polling()
        except Exception as ex:
            print(ex)
