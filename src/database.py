"""Модуль содержит класс для работы с базой данных на стороне сервера."""

import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Estimation, Product, Rating
from const import *


def create_database_name():
    """Функция создает путь к базе данных для сервера."""

    # Путь к базе данных на стороне сервера
    DIR_NAME = 'database'  # имя папки, в которую поместим базу данных
    DIR_PATH = os.path.join(os.getcwd(), DIR_NAME)
    if not os.path.exists(DIR_PATH):
        # Если папки для базы данных нет, создаем ее
        os.mkdir(DIR_PATH)
    DATABASE_NAME = 'db.sqlite3'  # имя базы данных
    return os.path.join(DIR_PATH, DATABASE_NAME)


class Database:
    """Класс для работы с базой данных на стороне сервера."""

    def __init__(self):
        """Конструктор."""

        db_name = create_database_name()  # получаем путь к базе данных
        engine = create_engine(f'sqlite:///{db_name}')
        Base.metadata.create_all(engine)
        # Создаем сессию
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def __del__(self):
        """Деструктор."""

        # Закрываем сессию
        self.session.close()

    def add_estimation(self, estimation_name, min_value=None, max_value=None):
        """Метод добавляет фильтр.
        :param estimation_name: название фильтра;
        :param min_rating, max_rating: минимальная и максимальная оценки товара
        по фильтру. Если min_rating = None, то нет минимального значения. Если
        max_value = None, то нет максимального значения.
        :return: данные добавленного фильтра, иначе None."""

        # Ищем фильтр в таблице фильтров
        n = self.session.query(Estimation).filter_by(
            name=estimation_name).count()
        if n:
            # Фильтр уже записан в базу данных
            return None
        # Фильтра в базе данных нет, добавляем
        e = Estimation(estimation_name, min_value, max_value)
        self.session.add(e)
        self.session.commit()
        return e.get()

    def add_product(self, product_name):
        """Метод добавляет товар в таблицу с товарами.
        :param product_name: наименование товара.
        :return product: данные добавленного товара, иначе None."""

        # Ищем товар в таблице с товарами
        n = self.session.query(Product).filter_by(name=product_name).count()
        if n:
            # Товар уже записан в базу данных
            return None
        # Товара в базе данных нет, добавляем
        product = Product(product_name)
        self.session.add(product)
        self.session.commit()
        return product.get()

    def add_rating(self, product_name, estimation_name, rating, address):
        """Метод добавляет оценку товара.
        :param product_name: наименование товара;
        :param estimation_name: фильтр, по которому оценивается товар;
        :param rating: оценка по фильтру;
        :param address: адрес магазина, в котором приобретен оцениваемый
        товар."""

        # Ищем товар в таблице товаров
        p = self.session.query(Product).filter_by(name=product_name).first()
        if not p:
            # Товара нет, нужно добавить
            p = self.add_product(product_name)
        # Ищем фильтр в таблице фильтров
        e = self.session.query(Estimation).filter_by(
            name=estimation_name).first()
        if e.min_value != None and rating < e.min_value:
            # Оценка по фильтру не может быть меньше минимального значения
            rating = e.min_value
        if e.max_value != None and rating > e.max_value:
            # Оценка по фильтру не может быть больше максимального значения
            rating = e.max_value
        # Добавляем оценку товара
        self.session.add(Rating(p, e, rating, address))
        self.session.commit()

    def change_estimation(self, estimation_name, min_value=None,
                          max_value=None):
        """Метод изменяет пределы значений оценки по фильтру.
        :param estimation_name: название фильтра;
        :param min_value, max_value: новые предельные значения оценки по
        фильтру."""

        # Изменяем предельные значения
        self.session.query(Estimation).filter_by(name=estimation_name).update(
            {Estimation.min_value: min_value, Estimation.max_value: max_value},
            synchronize_session=False)
        self.session.commit()

    def get_estimation(self, estimation_name):
        """Метод возвращает фильтр с заданным названием.
        :param estimation_name: название фильтра.
        :return: фильтр с заданным названием."""

        return self.session.query(Estimation).filter_by(
            name=estimation_name).first()

    def get_estimations(self):
        """Метод возвращает все фильтры.
        :return: список с названиями и пределами оценов для фильтров."""

        estimations = self.session.query(Estimation).all()
        return [e.get() for e in estimations]

    def get_estimation_limits(self, estimation_name):
        """Метод получает пределы значений оценки по фильтру.
        :param estimation_name: название фильтра;
        :return: кортеж из пределов значений оценки по фильтру."""

        e = self.session.query(Estimation).filter_by(
            name=estimation_name).first()
        if not e:
            return (None, None)
        return (e.min_value, e.max_value)

    def get_estimations_names(self):
        """Метод возвращает названия всех фильтров.
        :return: список с названиями всех фильтров."""

        estimations = self.session.query(Estimation).all()
        return [e.name for e in estimations]

    def get_product(self, product_name):
        """Метод возвращает товар с заданным названием.
        :param product_name: название товара.
        :return: товар с заданным названием."""

        return self.session.query(Product).filter_by(
            name=product_name).first()

    def get_products(self):
        """Метод возвращает все названия товаров.
        :return: список с названиями всех товаров."""

        products = self.session.query(Product).all()
        return [product.get() for product in products]

    def get_ratings(self, product_name, estimation_name):
        """Метод возвращает товары с определенным названием, оцененные по
        определенному фильтру.
        :param product_name: название товара;
        :param estimation_name: название фильтра.
        :return: список товаров с оценками."""

        p = self.session.query(Product).filter_by(name=product_name).first()
        e = self.session.query(Estimation).filter_by(
            name=estimation_name).first()
        if not p or not e:
            return []
        ratings = self.session.query(Rating).filter_by(
            product_id=p.id, estimation_id=e.id).order_by(Rating.rating).all()
        return [rating.get() for rating in ratings]

    def delete_product(self, product_name):
        """Метод удаляет товар из таблицы с названиями товаров.
        :param product_name: название удаляемого товара."""

        self.session.query(Product).filter_by(name == product_name).delete(
            synchronize_session=False)
        self.session.commit()

    def delete_rating(self, rating_id):
        """Метод удаляет оценку товара.
        :param rating_id: ID оценки товара."""

        self.session.query(Rating).filter_by(id == rating_id).delete(
            synchronize_session=False)
        self.session.commit()


if __name__ == "__main__":

    db = Database()
    # Добавляем фильтр по стоимости
    db.add_estimation('Стоимость', 0)
    # Добавляем фильтр по качетсву
    db.add_estimation('fddfd', None, None)
    # Получаем все фильтры
    estimations = db.get_estimations()
    print(estimations)
    # Получаем предельные значения оценки по фильтру
    print(db.get_estimation_limits(estimations[0][FILTER]))
    # Изменяем предельные значения оценки
    db.change_estimation(estimations[0][FILTER], 0)
    # Добавляем товар
    db.add_product('Сыр')
    # Добавляем оценку товара
    db.add_rating('Сыр', 'Стоимость', 672.8, 'Москва')
    print(db.get_ratings('Сыр', 'Стоимость'))
