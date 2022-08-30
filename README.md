# Instagram parsing bot

Бот предназначен для получения любых материалов (постов, stories, highlighs, reels) с публичных аккаунтов инстаграм анонимно. В боте также имеется система платной подписки (которая открывает доступ к боту после истечения пробного периода), реферальная система, возможность выбора из нескольких языков.
Для парсинга использует самописную "библиотеку", подделывающую запросы к апи инстаграм. Бот умеет применять прокси.
Без selenium и сторонних библиотек для работы с инстаграмом.

Проект написан давно и может не соответствать тому уровню качества кода, которого я стараюсь держаться на данный момент, о
нынешней ситуации лучше дадут понять более новые репозитории,
например [github.com/Bobako/sms_handler](https://github.com/Bobako/sms_handler).

Инструменты, использованные в проекте:

- Python (SQLAlchemy, TelegramBotAPI, Bottle, Requests а также менее значимые библиотеки)

Потрогать демку проекта можно [тут](http://t.me/ig_parsing_demo_bot). Для работы бота в демонстрационном режиме не используется прокси, так что не перебарщивайте с количеством запросов, а то перестанет работать по причине бана. 
Демка развернута на Ubuntu 20.04 средствами Supervisord.
