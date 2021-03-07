"""Модуль содержит полезные функции."""

import os
import sys
import time
import threading
import const as cn


def delete_file(path):
    """Функция удаляет файл и директорию, в которой находился этот файл.
    :param path: путь к удаляемому файлу."""

    # Удаляем файл
    os.remove(path)
    # Удаляем директорию
    os.rmdir(os.path.split(path)[0])


def determine_address():
    """Функция определяет IP адрес из командной строки. Строка для сервера
    и клиента должна быть записана в формате:
    server.py -p port -a ip_address
    client.py -p port -a ip_address
    Например:
    server.py -p 8078 -a 192.168.1.2
    client.py -p 8078 -a 192.168.1.2
    :return: IP адрес, который будет слушать сервер и на который должны
    отправлять сообщения клиенты."""

    try:
        if '-a' in sys.argv:
            address = sys.argv[sys.argv.index('-a') + 1]
        else:
            address = cn.DEFAULT_IP_ADDRESS
        return address
    except IndexError:
        sys.exit(1)


def determine_port():
    """Функция определяет порт для подключения. Строка для сервера и клиента
    должна быть записана в формате:
    server.py -p port -a ip_address
    client.py -p port -a ip_address
    Например:
    server.py -p 8078 -a 192.168.1.2
    client.py -p 8078 -a 192.168.1.2
    :return: порт."""

    try:
        if '-p' in sys.argv:
            port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            port = cn.DEFAULT_PORT
        if port < 1024 or port > 65535:
            raise ValueError
        return port
    except:
        sys.exit(1)


def find_socket(sockets, ip_address):
    """Функция находит сокет по IP адресу.
    :param sockets: список сокетов;
    :param ip_address: IP адрес.
    :return: найденный сокет или None, если сокет не найден."""

    for sock in sockets:
        if ip_address == get_socket_param(sock):
            return sock
    return None


def get_socket_param(sock):
    """Метод возвращает параметры сокета.
    :param sock: сокет.
    :return: IP адрес."""

    return str(sock.getpeername())


def get_time():
    """Функция получает текущее время."""

    return time.strftime('%Y-%m-%d %H:%M:%S')


def printf(text):
    """Функция для вывода текста в специальном формате.
    :param text: текст, который нужно вывести на экран."""

    print(f'[{get_time()}][{text}]')


def thread(func):
    """Декоратор для запуска функции в отдельном потоке."""
    def wrapper(*args, **kwargs):
        new_thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        new_thread.start()
        return new_thread
    return wrapper


def validate(func):
    """Декоратор выполняет валидацию клиента в базе данны."""
    def wrapper(*args, **kwargs):

        return func(*args, **kwargs)
    return wrapper
