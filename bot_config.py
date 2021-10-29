# DATABASE CONFIG
DB_LOGIN = "alex"
DB_PASSWORD = "otvertka"
DB_ADDRESS = "localhost"
DB_NAME = "test_db"

# PREMIUM CONFIGS
TRIAL_PERIOD_SECONDS = 3600 * 24
REFERER_PERIOD_SECONDS = 3600 * 24
PAYED_PERIOD_SECONDS_PRICES = [
    {"period": 3600 * 24, "price": 49},
    {"period": 3600 * 24 * 3, "price": 129},
    {"period": 3600 * 24 * 7, "price": 299},
]
PAYMENT_DOMAIN = "https://example.com"
PAYMENT_PATH = "/payment"

BOT_DOMAIN = "localhost"
BOT_PORT = 8080
BOT_PAYMENT_ROUTE = "/payment_callback"


# BOT CONFIG
BOT_TOKEN = "2093517269:AAHbdc1UiEzgpkZJQP7njMn3OT8eXAcbm60"
ELEMENTS_PER_PAGE = 9
REELS_PER_PAGE = 5  # если поставить больше, начианет рассыпаться сообщение при пагинации(
MAX_SYMBOLS_PREVIEW = 100
PLACEHOLDER_IMAGE_PATH = "./placeholder.jpg"

# PARSER CONFIG
IG_LOGIN = 'aleksandr.shishiga'
IG_PASSWORD = 'otvertka'
PROXY_ADDR = None
SAVE_DIRECTORY = "./media/"
POSTS_LIMIT = 112
SUBSCRIPTION_CHECK_PERIOD = 3600 * 4

# LANGUAGE CONFIGS
DEFAULT_LANGUAGE = 'ru'

MSGS = {
    'ru': {
        'icon': "🇷🇺",
        'lang_updated': "Язык был изменен на русский",
        'skip': "Пропустить",
        'thanks': "Спасибо!",
        'choice': "Выбрать",
        'hide': "Спрятать",
        'paginator': "Страница {} из {}",
        "post_info": 'Опубликовано в {}, лайков: {}, комментариев: {}.',
        'IGRedirectError': 'Сожалеем, возникла ошибка(\n Мы работаем над этим',
        'NoSuchUserError': 'Нам не удалось найти пользователя с таким именем в Instagram.\n'
                           'Проверьте, правильно ли вы ввели имя',
        'NoMaterialsFoundError': "На данный момент у этого пользователя нет материалов",
        'NoHistoryError': "Нет результатов",
        'START_MSG': 'Привет! Выберите язык',
        'REF_MSG': 'Если кто-то рассказал вам об этом боте, укажите его @ник:',
        'HELP_MSG': 'Это бот для получения материалов из Instagram. Функционал:\n'
                    '/stories - получить сторис пользователя \n\n'
                    '/posts - получить посты пользователя \n\n'
                    '/reels - получить reels пользователя \n\n'
                    '/highlights - получить highlights пользователя \n\n'
                    '/subscribe - подписаться на пользователся и получать все его обновления \n\n'
                    '/history - история вашего поиска \n\n'
                    '/help - вызвать это меню\n\n'
                    '/language - сменить язык\n\n'
                    '/support - написать разработчику\n\n'
                    '/premium - оплатить доступ к боту. Сейчас бот доступен вам до {}',
        'INPUT_USERNAME_MSG': "Введете имя пользователя instagram",
        'SUBSCRIPTION_MSG': "Вы будете получать обновления {}. Вы всегда можете отписаться от обновлений - /unsubscribe",
        'UNSUBSCRIPTION_MSG': "Вы больше не будете получать обновления {}.",
        "PREMIUM_EXPIRED_MSG": "Ваш срок доступа к боту истек(\nПолучить еще - /premium",
        "SUBSCRIPTION_UPDATE_MSG": "{} опубликовал новые материалы:",
        "PREMIUM_MSG": "Продлить доступ к боту",
        "PREMIUM_OPTION": "{} дня за {}",
        "PREMIUM_PROCEED_PAYMENT": "Платеж обрабатывается",
        "PREMIUM_ADDED": "Доступ к боту был продлен. Спасибо!\nСейчас бот доступен вам до {}",
        "PAYMENT_ERROR": "Ошибка обработки платежа(",
        "SUPPORT_MSG": "https://t.me/b0bak0",
    },
    'en': {
        'icon': "🇬🇧",
        'lang_updated': "Language was set to english",
        'skip': "Skip",
        'thanks': "Thanks!",
        'choice': "More",
        "hide": "Hide",
        "paginator": 'Page {} out of {}',
        "post_info": 'Published at {}, likes: {}, comments: {}.',
        'IGRedirectError': 'Sorry, an error has occurred(\n We are working on it',
        'NoSuchUserError': "We couldn't find a user with that name on Instagram.\n"
                           "Check if you entered the name correctly",
        'NoMaterialsFoundError': "At the moment, this user has no materials",
        'NoHistoryError': "No results",
        'START_MSG': 'Hello! Choose language',
        "REF_MSG": 'If someone told you about this bot, specify his @nickname',
        "HELP_MSG": 'This is a bot for getting stuff from Instagram. Functional:\n'
                    '/stories - get the users stories \n'
                    '/posts - get user posts \n'
                    '/reels - get users reels \n'
                    '/highlights - get user highlights \n'
                    '/subscribe - subscribe to the user and receive all his updates \n'
                    '/history - your search history \n'
                    '/help - this menu\n'
                    '/language - change language\n'
                    '/support - tech support\n'
                    '/premium - pay for access to the bot. Now you have access till {}',
        'INPUT_USERNAME_MSG': "Input instagram username",
        'SUBSCRIPTION_MSG': "You will receive {}'s updates. You can always unsubscribe from updates - /unsubscribe",
        'UNSUBSCRIPTION_MSG': "You will no longer receive {}'s updates",
        "PREMIUM_EXPIRED_MSG": "Your access period to the bot has expired (\nGet more - /premium",
        "SUBSCRIPTION_UPDATE_MSG": "{} has new publications:",
        "PREMIUM_MSG": "Extend access",
        "PREMIUM_OPTION": "{} days for {}",
        "PREMIUM_PROCEED_PAYMENT": "Payment is being proceed",
        "PREMIUM_ADDED": "Your access to the bot was extended, thanks!\nNow you have access till {}",
        "PAYMENT_ERROR": "Error during payment handling",
        "SUPPORT_MSG": "https://t.me/b0bak0",
    }
}
