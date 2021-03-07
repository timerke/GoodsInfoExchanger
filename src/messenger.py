"""Модуль содержит определение класса для отправки и получения сообщений между
клиентом и сервером."""

import json
import struct
from const import ENCODING


class Messenger:
    """Класс для отправки и получения сообщений между клиентом и сервером."""

    def __init__(self):
        """Конструктор."""

        pass

    def get_msg(self, sock):
        """Метод принимает и декодирует сообщение.
        :param sock: сокет, откуда получается сообщение.
        :return: полученное сообщение-словарь."""

        # Получаем закодированное сообщение-словарь
        encoded_msg = self.receive_all_msg(sock)
        if not isinstance(encoded_msg, bytes):
            # Если encoded_msg не является закодированным объектом, это ошибка
            raise ValueError
        # Сообщение декодируется
        json_msg = encoded_msg.decode(ENCODING)
        # JSON-сообщение преобразовывается в словарь
        msg = json.loads(json_msg)
        # Получаем бинарный файл, присланный вместе с сообщением-словарем
        return msg

    def receive_all_msg(self, sock):
        """Метод для чтения всего сообщения.
        :param sock: сокет, откуда получается сообщение.
        :return: полученное сообщение."""

        # Получаем длину сообщения-словаря
        raw_msg_len = self.receive_given_size_msg(sock, 4)
        msg_len = struct.unpack('>I', raw_msg_len)[0]
        # Получаем словарь-сообщение и бинарный файл
        return self.receive_given_size_msg(sock, msg_len)

    def receive_given_size_msg(self, sock, n):
        """Метод для чтения сообщения заданного размера.
        :param sock: сокет, откуда читается сообщение;
        :param n: размер сообщения, которое нужно прочесть.
        :return: прочтенное сообщение."""

        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def send_msg(self, sock, message):
        """Метод кодирует и отправляет сообщение. Протокол отправки сообщений
        следующий. Сначала отправляются 4 байта с размером словаря-сообщения,
        а потом отправляется словарь-сообщение.
        :param sock: сокет, куда отправляется сообщение;
        :param message: словарь-сообщение для отправки."""

        # Словарь-сообщение преобразовывается в JSON-объект и кодируется
        json_msg = json.dumps(message)
        encoded_msg = json_msg.encode(ENCODING)
        # Получаем массив из префикса в 4 байт длиной (в котором длина словаря-
        # сообщения) и словаря-сообщения
        msg = struct.pack('>I', len(encoded_msg)) + encoded_msg
        # Отправляем сообщение
        while msg:
            # Количество отправленных байт
            sent_num = sock.send(msg)
            msg = msg[sent_num:]
