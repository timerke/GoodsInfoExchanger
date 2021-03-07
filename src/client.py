"""Программа-клиент."""

import json
import socket
import sys
import time
import threading
from datetime import datetime
from PyQt5.QtCore import pyqtSignal, QObject
import const as cn
from messenger import Messenger
from utilities import *


# Семафор для потока с отправкой сообщений
sender_semaphore = threading.Semaphore(0)
# Ключи для потоков для установки соединения с сервером, для получения и
# отправки сообщений на сервер
TH_CONNECT = 'connect'
TH_PROCESS = 'process'
TH_SEND = 'send'


class Client(QObject):
    """Класс для работы с клиентом."""

    # Сигнал для отправки сообщений в главное окно
    signal_to_send = pyqtSignal(dict)

    def __init__(self):
        """Конструктор.
        :param wnd: ссылка на окно приложения."""

        super().__init__()
        # Сигнал о наличии соединения с сервером
        self.connected = threading.Event()
        # Объект для отправки/получения сообщений от сервера
        self.messenger = Messenger()
        # Словарь с потоками
        self.threads = {TH_CONNECT: None, TH_PROCESS: None, TH_SEND: None}

    @thread
    def connect(self):
        """Метод подключает клиента к серверу."""

        printf('Запущено соединение с сервером')
        self.connected.clear()  # нет соединения
        while not self.connected.is_set():
            # Определяются порт и IP адрес сервера
            self.server_addr = determine_address()
            self.server_port = determine_port()
            # Инициализация сокета
            self.server_sock = socket.socket(socket.AF_INET,
                                             socket.SOCK_STREAM)
            try:
                self.server_sock.connect((self.server_addr, self.server_port))
                self.connected.set()  # есть соединение
                printf('Установлено соединение')
            except ConnectionRefusedError:
                # Ошибка при подключении к серверу
                time.sleep(1)
        # Создаем два потока: для чтения и для отправки сообщений
        if not self.threads[TH_PROCESS] or not self.threads[TH_PROCESS].is_alive():
            self.threads[TH_PROCESS] = self.process_msg()
        if not self.threads[TH_SEND] or not self.threads[TH_SEND].is_alive():
            self.threads[TH_SEND] = self.send_msg()

    def create_msg(self, data):
        """Метод создает сообщение для отправки на сервер.
        :param data: данные для отправки."""

        self.msg = data
        sender_semaphore.release()

    @thread
    def process_msg(self):
        """Метод разбирает сообщение из сервера."""

        printf('Запущен поток для чтения сообщений')
        # Цикл продолжается, пока есть соединение с сервером
        while self.connected.is_set():
            try:
                msg = self.messenger.get_msg(self.server_sock)
                action = msg.get(cn.ACTION)
                if action:
                    printf(f'Клиент получил сообщение: {msg}')
                    self.signal_to_send.emit(msg)
            except BaseException:
                # Произошла ошибка, которую считаем ошибкой подключения к
                # серверу
                self.connected.clear()
        printf('Поток для чтения сообщений завершен')
        # Запускаем соединение с сервером
        self.connect()

    @thread
    def send_msg(self):
        """Метод отправляет сообщения на сервер."""

        printf('Запущен поток для отправки сообщений')
        # Цикл продолжается, пока есть соединение с сервером
        while self.connected.is_set():
            try:
                sender_semaphore.acquire()
                printf(f'Клиент отправляет сообщение: {self.msg}')
                self.messenger.send_msg(self.server_sock, self.msg)
            except BaseException:
                # Произошла ошибка, которую считаем ошибкой подключения к
                # серверу
                self.connected.clear()
        printf('Поток для отправки сообщений завершен')
        # Запускаем соединение с сервером
        self.connect()


if __name__ == '__main__':

    client = Client()
    client.connect()
