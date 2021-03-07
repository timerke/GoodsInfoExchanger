"""Модуль содержит основные константы, используемые в сервисе."""

# Параметры сетевого соединения
DEFAULT_PORT = 7777  # порт по умолчанию
DEFAULT_IP_ADDRESS = '127.0.0.1'  # IP адрес по умолчанию
MAX_CONNECTIONS = 5  # максимальная очередь подключений
MAX_PACKAGE_LENGTH = 1024  # максимальная длинна сообщения в байтах

# Кодировка проекта
ENCODING = 'utf-8'

# Протокол JSON Instant Messaging, основные ключи
ACTION = 'action'  # тип сообщения
ADDRESS = 'address'
CONTENT = 'content'
DATE = 'date'
FILTER = 'filter'  # фильтр
ID = 'id'  # идентификатор
IP = 'ip'
MAX = 'max' # максимальное значение оценки
MIN = 'min' # минимальное значение оценки
MSG = 'msg'
PRODUCT = 'product'  # товар
RATING = 'rating'
SOCKET = 'socket'
STATUS = 'status'  # статус

# Значения поля ACTION:
# Добавление нового фильтра
ADD_FILTER = 'add_filter'
# Добавление нового товара
ADD_PRODUCT = 'add_product'
# Добавление новой оценки товара
ADD_RATING = 'add_rating'
# Получение названий фильтров и товаров
GET_FILTERS_AND_PRODUCTS = 'get_filters_and_products'
# Получение оценок товара по заданному фильтру
GET_RATINGS = 'get_ratings'
