"""Модуль содержит модели таблиц из базы данных."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.orm import relationship
from const import *

Base = declarative_base()


class Estimation(Base):
    """Модель таблицы с фильтрами для товаров."""

    __tablename__ = 'estimation'
    id = Column(Integer, autoincrement=True, primary_key=True)
    # Название фильтра
    name = Column(String, nullable=False, unique=True)
    # Минимальная оценка по фильтру
    min_value = Column(Float, default=None)
    # Максимальная оценка по фильтру
    max_value = Column(Float, default=None)

    def __init__(self, estimation_name, min_value, max_value):
        """Конструктор.
        :param estimation: название фильтра;
        :param min_value, max_value: минимальная и максимальная оценки товара
        по фильтру. Если min_rating = None, то нет минимального значения. Если
        max_value = None, то нет максимального значения."""

        self.name = estimation_name
        self.min_value = min_value
        self.max_value = max_value

    def __repr__(self):
        return f'<Estimation({self.name})>'

    def get(self):
        """Метод возвращает словарь из ID, названия и пределов оценок для
        фильтра."""

        return {ID: self.id, FILTER: self.name, MIN: self.min_value,
                MAX: self.max_value}


class Product(Base):
    """Модель таблицы с товарами."""

    __tablename__ = 'product'
    id = Column(Integer, autoincrement=True, primary_key=True)
    # Название товара
    name = Column(String, nullable=False, unique=True)

    def __init__(self, product_name):
        """Конструктор.
        :param product_name: название товара."""

        self.name = product_name

    def __repr__(self):
        return f'<Product({self.name})>'

    def get(self):
        """Метод возвращает словарь из ID и названия товара."""

        return {ID: self.id, PRODUCT: self.name}


class Rating(Base):
    """Модель таблицы с оценками товаров по разным фильтрам."""

    __tablename__ = 'rating'
    id = Column(Integer, autoincrement=True, primary_key=True)
    # Ссылка на товар
    product_id = Column(Integer, ForeignKey('product.id'), nullable=False)
    # Ссылка на фильтр, по которому оценивается товар
    estimation_id = Column(Integer, ForeignKey('estimation.id'),
                           nullable=False)
    # Оценка товара по выбранному фильтру
    rating = Column(Float)
    # Адрес магазина, в котором приобретен товар
    address = Column(String, nullable=False)
    # Дата оценки товара
    date = Column(DateTime, nullable=False, default=datetime.now)

    def __init__(self, product, estimation, rating, address):
        """Конструктор.
        :param product: товар - объект типа Product;
        :param estimation: фильтр - объект типа Estimation;
        :param rating: оценка товара по выбранному фильтру;
        :param address: адрес магазина, в котором приобретен товар."""

        self.product_id = product.id
        self.estimation_id = estimation.id
        self.rating = rating
        self.address = address

    def __repr__(self):
        return f'<Rating({self.product_id}, {self.estimation_id}, {self.rating})>'

    def get(self):
        """Метод возвращает словарь из данных оценки товара."""

        return {ID: self.id, ADDRESS: self.address, RATING: self.rating,
                DATE: self.date.strftime('%Y-%m-%d %H:%M:%S')}
