"""Программа-сервер."""

import select
import socket
from datetime import datetime
import const as cn
from database import Database
from messenger import Messenger
from utilities import *


class Server():
    """Класс для работы с сервером."""

    def __init__(self):
        """Конструктор."""

        # Определяем порт и IP адрес для сервера
        self.listen_port = determine_port()
        self.listen_addr = determine_address()
        # Инициализация сокета для соединения по TCP протоколу
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.listen_addr, self.listen_port))
        # Слушается порт
        self.sock.listen(cn.MAX_CONNECTIONS)
        self.sock.settimeout(0.1)
        printf('Сервер запущен')
        # Объект для работы с базой данных
        self.db = Database()
        # Добавляем несколько фильтров и товаров в базу данных
        self.init_db()
        # Объект для приема/отправки сообщений
        self.messenger = Messenger()

    def init_db(self):
        """Метод добавляет несколько фильтров и товаров в базу данных."""

        # Фильтры
        self.db.add_estimation('Стоимость', 0)
        self.db.add_estimation('Качество', 0, 10)
        # Товары
        self.db.add_product('Сыр')
        self.db.add_product('Хлеб')
        self.db.add_product('Молоко')

    def process_add_estimation(self, msg, sock, tasks):
        """Метод обрабатывает запрос на добавление нового фильтра.
        :param msg: сообщение от клиента;
        :param sock: сокет клиента;
        :param tasks: список задач по отправке сообщений из сервера
        клиентам."""

        # Получаем информацию из сообщения
        content = msg.get(cn.CONTENT)
        estimation_name = content.get(cn.FILTER)
        min_value = content.get(cn.MIN)
        max_value = content.get(cn.MAX)
        # Заготовка ответа
        response = {cn.ACTION: cn.ADD_FILTER,
                    cn.STATUS: 400}
        if estimation_name:
            # Добавляем фильтр
            estimation = self.db.add_estimation(estimation_name, min_value,
                                                max_value)
            if estimation:
                # Фильтр добавлен
                response[cn.STATUS] = 200
                response[cn.CONTENT] = estimation
        # Добавляем задачу отправки ответа клиенту
        tasks.append({cn.SOCKET: sock, cn.MSG: response})

    def process_add_product(self, msg, sock, tasks):
        """Метод обрабатывает запрос на добавление нового товара.
        :param msg: сообщение от клиента;
        :param sock: сокет клиента;
        :param tasks: список задач по отправке сообщений из сервера
        клиентам."""

        # Получаем информацию из сообщения
        content = msg.get(cn.CONTENT)
        product_name = content.get(cn.PRODUCT)
        # Заготовка ответа
        response = {cn.ACTION: cn.ADD_PRODUCT,
                    cn.STATUS: 400}
        if product_name:
            # Добавляем товар
            product = self.db.add_product(product_name)
            if product:
                # Товар добавлен
                response[cn.STATUS] = 200
                response[cn.CONTENT] = product
        # Добавляем задачу отправки ответа клиенту
        tasks.append({cn.SOCKET: sock, cn.MSG: response})

    def process_add_rating(self, msg, sock, tasks):
        """Метод обрабатывает запрос на добавление оценки товара.
        :param msg: сообщение от клиента;
        :param sock: сокет клиента;
        :param tasks: список задач по отправке сообщений из сервера
        клиентам."""

        # Получаем информацию из сообщения
        content = msg.get(cn.CONTENT)
        product_name = content.get(cn.PRODUCT)
        estimation_name = content.get(cn.FILTER)
        address = content.get(cn.ADDRESS)
        rating = content.get(cn.RATING)
        date = content.get(cn.DATE)
        # Заготовка ответа
        response = {cn.ACTION: cn.ADD_RATING,
                    cn.STATUS: 400}
        if product_name and estimation_name and address and rating and date:
            # Добавляем оценку
            self.db.add_rating(product_name, estimation_name, rating, address)
            # Получаем оценки товара по фильтру
            ratings = self.db.get_ratings(product_name, estimation_name)
            response[cn.STATUS] = 200
            response[cn.CONTENT] = ratings
        # Добавляем задачу отправки ответа клиенту
        tasks.append({cn.SOCKET: sock, cn.MSG: response})

    def process_get_estimations_and_products(self, msg, sock, tasks):
        """Метод обрабатывает запрос на получение всех фильтров и товаров.
        :param msg: сообщение от клиента;
        :param sock: сокет клиента;
        :param tasks: список задач по отправке сообщений из сервера
        клиентам."""

        # Получаем данные о фильтрах
        estimations = self.db.get_estimations()
        # Получаем названия товаров
        products = self.db.get_products()
        task = {cn.SOCKET: sock,
                cn.MSG: {cn.ACTION: cn.GET_FILTERS_AND_PRODUCTS,
                         cn.STATUS: 200,
                         cn.CONTENT: {cn.FILTER: estimations,
                                      cn.PRODUCT: products}}}
        tasks.append(task)

    def process_get_ratings(self, msg, sock, tasks):
        """Метод обрабатывает запрос на получение оценок товаров по заданному
        фильтру.
        :param msg: сообщение от клиента;
        :param sock: сокет клиента;
        :param tasks: список задач по отправке сообщений из сервера
        клиентам."""

        # Получаем информацию из сообщения
        content = msg.get(cn.CONTENT, {})
        product_name = content.get(cn.PRODUCT)
        estimation_name = content.get(cn.FILTER)
        # Заготовка ответа
        response = {cn.ACTION: cn.GET_RATINGS,
                    cn.STATUS: 400}
        # Получаем оценки товара по фильтру
        ratings = self.db.get_ratings(product_name, estimation_name)
        if ratings:
            # Формируем ответ
            response[cn.STATUS] = 200
            response[cn.CONTENT] = ratings
        # Добавляем задачу отправки ответа клиенту
        tasks.append({cn.SOCKET: sock, cn.MSG: response})

    def process_msg(self, msg, sock, tasks):
        """Метод обрабатывает сообщение от клиента.
        :param msg: словарь-сообщение от клиента;
        :param sock: сокет клиента, от кого получено сообщение;
        :param tasks: список задач по отправке сообщений из сервера
        клиентам."""

        action = msg.get(cn.ACTION)
        if action == cn.ADD_FILTER:
            # Запрос на добавление нового фильтра
            return self.process_add_estimation(msg, sock, tasks)
        if action == cn.ADD_PRODUCT:
            # Запрос на добавление нового товара
            return self.process_add_product(msg, sock, tasks)
        if action == cn.ADD_RATING:
            # Запрос на добавление оценки товара
            return self.process_add_rating(msg, sock, tasks)
        if action == cn.GET_FILTERS_AND_PRODUCTS:
            # Запрос на получение всех фильтров и товаров
            return self.process_get_estimations_and_products(msg, sock, tasks)
        if action == cn.GET_RATINGS:
            # Запрос на получение оценок товара по заданному фильтру
            return self.process_get_ratings(msg, sock, tasks)

    def read_messages(self, clients_read, all_clients, tasks):
        """Метод читает сообщения от клиентов.
        :param clients_read: список сокетов клиентов, сообщения от которых
        нужно прочитать;
        :param all_clients: список всех сокетов клиентов;
        :param tasks: список задач по отправке сообщений из сервера
        клиентам."""

        for sock in clients_read:
            try:
                # Сообщение от клиента и его IP адрес
                ip_address = get_socket_param(sock)
                msg = self.messenger.get_msg(sock)
                printf(f'Клиент с адресом {ip_address} прислал сообщение: '
                       f'{msg}')
                # Обрабатываем сообщение
                self.process_msg(msg, sock, tasks)
            except Exception:
                # Не удалось прочесть сообщение от клиента, потому что клиент
                # вышел из сети
                all_clients.remove(sock)
                printf(f'Клиент с адресом {ip_address} отключился')

    def write_responses(self, clients_write, all_clients, tasks):
        """Метод отправляет ответы клиентам, которым это нужно.
        :param clients_write: список сокетов клиентов, ожидающих получения
        сообщения;
        :param all_clients: список сокетов всех клиентов;
        :param tasks: список задач по отправке сообщений из сервера
        клиентам."""

        while tasks:
            # Берем первую в списке задачу
            task = tasks[0]
            # Сокет клиента и его IP адрес
            sock = task[cn.SOCKET]
            ip_address = get_socket_param(sock)
            # Сообщение для отправки
            msg = task[cn.MSG]
            try:
                # Отправляем сообщение
                self.messenger.send_msg(sock, msg)
                printf(f'Клиенту с адресом {ip_address} отправлено сообщение:'
                       f' {msg}')
            except Exception:
                # Сообщение не удалось отправить, так как клиент отключился
                all_clients.remove(sock)
                printf(f'Клиент с адресом {ip_address} отключился')
            finally:
                del tasks[0]


def run():
    """Функция запускает сервер."""

    # Создаем объект-сервер
    server = Server()
    all_clients = []  # список для всех клиентов
    # Список задач по отправке сообщений. Каждая задача - словарь в формате
    # {sock: сокет клиента, MSG: сообщение-словарь, которое нужно отправить}
    tasks = []
    while True:
        try:
            client_sock, _ = server.sock.accept()
            ip_address = get_socket_param(client_sock)
            printf(f'Подключился клиент с адресом {ip_address}')
        except OSError:
            pass
        else:
            # Добавляем клиента
            all_clients.append(client_sock)
        finally:
            clients_read = []  # список сокетов для клиентов, ожидающих чтения
            clients_write = []  # список сокетов для клиентов, ожидающих записи
            try:
                clients_read, clients_write, errors = select.select(
                    all_clients, all_clients, [], 0)
            except Exception:
                pass
            server.read_messages(clients_read, all_clients, tasks)
            if tasks:
                server.write_responses(clients_write, all_clients, tasks)


if __name__ == '__main__':
    run()
