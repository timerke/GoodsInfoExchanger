"""Модуль содержит определение класса окна с графическим интерфейсом для
клиентского приложения."""

import os
import sys
from datetime import datetime
import PyQt5.QtWidgets as qt
from PyQt5.QtCore import QRegExp, Qt, QObject, pyqtSignal, QEvent
from PyQt5.QtGui import QIcon, QDoubleValidator, QRegExpValidator
import const as cn
from client import Client
from utilities import *


class Filter_dialog(qt.QDialog):
    """Класс для диалогового окна для ввода данных о новом фильте."""

    def __init__(self, parent=None):
        """Конструктор."""

        super().__init__(parent=parent)
        self.setWindowIcon(QIcon('data/icon.png'))
        self.setWindowTitle('Добавить фильтр')
        self.setStyleSheet('background-color: #51cced;')
        btns = qt.QDialogButtonBox.Ok | qt.QDialogButtonBox.Cancel

        self.buttonBox = qt.QDialogButtonBox(btns)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        form = qt.QFormLayout()
        # Название нового фильтра
        self.filter = qt.QLineEdit()
        self.filter.setStyleSheet('background-color: white;')
        form.addRow('Название фильтра', self.filter)
        # Предельные значения
        self.min = qt.QLineEdit()
        self.min.setStyleSheet('background-color: white;')
        validator = QRegExpValidator(QRegExp('^[-]?\d+\.?\d*'), self)
        self.min.setValidator(validator)
        form.addRow('Минимальное значение', self.min)
        self.max = qt.QLineEdit()
        self.max.setStyleSheet('background-color: white;')
        self.max.setValidator(validator)
        form.addRow('Максимальное значение', self.max)
        vbox = qt.QVBoxLayout()
        vbox.addLayout(form)
        vbox.addWidget(self.buttonBox)
        self.setLayout(vbox)


class Window(qt.QMainWindow):
    """Класс окна клиента с графическим интерфейсом."""

    # Сигнал для связи с объектом типа Client для обмена данными
    signal_to_send = pyqtSignal(dict)

    def __init__(self, client):
        """Конструктор.
        :param client: ссылка на объект для чтения/отправки сообщений."""

        super().__init__()
        self.init_ui()
        # Связываем взаимно сигналы
        self.signal_to_send.connect(client.create_msg)
        client.signal_to_send.connect(self.process_data)
        # Задаем всем атрибутам окна исходные значения
        self.set_to_default()
        # Запрос на получение товаров и фильтров
        self.signal_to_send.emit({cn.ACTION: cn.GET_FILTERS_AND_PRODUCTS})

    def add_filter(self):
        """Метод выполняется для добавления нового фильтра."""

        # Показываем диалоговое окно для ввода данных о новом фильтре
        dialog = Filter_dialog()
        if not dialog.exec_():
            return
        # Название нового фильтра
        filter_name = dialog.filter.text()
        # Минимальное значение
        try:
            min_value = float(dialog.min.text())
        except:
            min_value = None
        # Максимальное значение
        try:
            max_value = float(dialog.max.text())
        except:
            max_value = None
        if min_value and max_value:
            # Проверяем, что минимальное значение меньше максимального
            if min_value > max_value:
                spam = max_value
                max_value = min_value
                min_value = spam
        # Отправляем сообщение на сервер
        msg = {cn.ACTION: cn.ADD_FILTER,
               cn.CONTENT: {cn.FILTER: filter_name,
                            cn.MIN: min_value,
                            cn.MAX: max_value}}
        self.signal_to_send.emit(msg)

    def add_product(self):
        """Метод выполняется для добавления нового товара."""

        # Показываем диалоговое окно для ввода данных о новом фильтре
        product_name, ok = qt.QInputDialog.getText(self, 'Добавить товар',
                                                   'Название товара')
        if not ok:
            return
        # Отправляем сообщение на сервер
        msg = {cn.ACTION: cn.ADD_PRODUCT,
               cn.CONTENT: {cn.PRODUCT: product_name}}
        self.signal_to_send.emit(msg)

    def change_combobox(self, i):
        """Метод вызывается при выборе нового пункта в выпадающем меню с
        товарами и фильтрами."""

        if self.sender() == self.wnd_1_filters:
            # Изменился выбранный фильтр из выпадающего списка
            self.check_rating()
            if i == len(self.filters):
                # Выбран пункт Другой фильтр
                self.add_filter()
                return
        elif self.sender() == self.wnd_1_products:
            # Изменился выбранный товар из выпадающего списка
            if i == len(self.products):
                # Выбран пункт Другой товар
                self.add_product()
                return
        # Получаем рейтинг товара по фильтру
        self.get_ratings()

    def check_rating(self):
        """Метод проверяет значение, введенное в поле оценки товара."""

        i = self.wnd_1_filters.currentIndex()
        if i < len(self.filters):
            try:
                rating = float(self.wnd_1_rating.text())
            except:
                return
            if ((self.filters[i][cn.MIN] != None and rating < self.filters[i][cn.MIN]) or
                    (self.filters[i][cn.MAX] != None and rating > self.filters[i][cn.MAX])):
                self.wnd_1_rating.setStyleSheet('background-color: pink;')
                self.btn.setEnabled(False)
            else:
                self.wnd_1_rating.setStyleSheet('background-color: white;')
                self.btn.setEnabled(True)

    def estimate(self):
        """Метод вызывается при клике по кнопке 'Оценить'."""

        # Получаем значения
        product = self.wnd_1_products.currentText()
        filter = self.wnd_1_filters.currentText()
        address = self.wnd_1_address.text()
        rating = None
        try:
            rating = float(self.wnd_1_rating.text())
        except:
            pass
        # Проверяем, что введены заполнены все поля
        if (product == 'Другой' or filter == 'Другой' or not address or
                rating == None):
            # Не введены все необходимые поля
            qt.QMessageBox.about(self, 'Информация',
                                 'Нужно заполнить все поля')
            return
        # Формируем запрос
        msg = {cn.ACTION: cn.ADD_RATING,
               cn.CONTENT: {cn.PRODUCT: product,
                            cn.FILTER: filter,
                            cn.ADDRESS: address,
                            cn.RATING: rating,
                            cn.DATE: get_time()}}
        self.signal_to_send.emit(msg)

    def get_ratings(self):
        """Метод отправляет запрос для получения рейтинга товара по фильтру."""

        if self.stacked_layout.currentIndex() == 0:
            product_name = self.wnd_0_products.currentText()
            filter_name = self.wnd_0_filters.currentText()
        else:
            product_name = self.wnd_1_products.currentText()
            filter_name = self.wnd_1_filters.currentText()
        msg = {cn.ACTION: cn.GET_RATINGS,
               cn.CONTENT: {cn.PRODUCT: product_name,
                            cn.FILTER: filter_name}}
        self.signal_to_send.emit(msg)

    def init_menu(self):
        """Метод создает меню и панель инструментов."""

        # Пункт меню Файл/Показать рейтинг
        show_rating_action = qt.QAction(QIcon('data/icon1.png'),
                                        'Показать рейтинг', self)
        show_rating_action.setStatusTip(
            'Показать рейтинг товара по оценкам пользователей')
        show_rating_action.triggered.connect(self.switch_wnd)
        # Пункт меню Файл/Оценить
        add_rating_action = qt.QAction(QIcon('data/icon2.png'), 'Оценить',
                                       self)
        add_rating_action.setStatusTip('Оценить товар')
        add_rating_action.triggered.connect(self.switch_wnd)
        # Пункт меню Файл/Добавить товар
        add_product_action = qt.QAction(QIcon('data/icon3.png'),
                                        'Добавить товар', self)
        add_product_action.setStatusTip('Добавить новый товар')
        add_product_action.triggered.connect(self.add_product)
        # Пункт меню Файл/Добавить фильтр
        add_filter_action = qt.QAction(QIcon('data/icon4.png'),
                                       'Добавить фильтр', self)
        add_filter_action.setStatusTip('Добавить фильтр для оценки товаров')
        add_filter_action.triggered.connect(self.add_filter)
        # Пункт меню Файл/Выйти
        exit_action = qt.QAction('Выйти', self)
        exit_action.setStatusTip('Выйти')
        exit_action.triggered.connect(self.close)
        # Добавляем меню Файл
        menubar = self.menuBar()
        menu_file = menubar.addMenu('Файл')
        menu_file.addAction(show_rating_action)
        menu_file.addAction(add_rating_action)
        menu_file.addSeparator()
        menu_file.addAction(add_product_action)
        menu_file.addAction(add_filter_action)
        menu_file.addSeparator()
        menu_file.addAction(exit_action)
        # Пункт меню Информация/О программе
        about = qt.QAction('О программе', self)
        about.setStatusTip('О программе')
        about.triggered.connect(self.show_info)
        # Добавляем меню Информация
        menu_info = menubar.addMenu('Информация')
        menu_info.addAction(about)

        # Панель инструментов
        self.toolbar = self.addToolBar('Панель инструментов')
        self.toolbar.addAction(show_rating_action)
        self.toolbar.addAction(add_rating_action)
        self.toolbar.addAction(add_product_action)
        self.toolbar.addAction(add_filter_action)

    def init_ui(self):
        """Метод инициализирует виджеты окна."""

        # Исходные размеры и положение окна
        self.resize(600, 500)
        self.move(300, 300)
        # Задаем название и иконку
        self.setWindowTitle('GoodsInfoExchanger')
        self.setWindowIcon(QIcon('data/icon.png'))
        self.setStyleSheet('background-color: #51cced;')
        # Меню
        self.init_menu()
        # Строка состояния
        self.status_bar = qt.QStatusBar()
        self.setStatusBar(self.status_bar)
        # Создаем все необходимые макеты окна
        self.stacked_layout = qt.QStackedLayout()
        self.stacked_layout.addWidget(self.init_wnd_0())
        self.stacked_layout.addWidget(self.init_wnd_1())
        self.stacked_layout.setCurrentIndex(0)
        # Добавляем все макеты к главному окну
        widget = qt.QWidget()
        widget.setLayout(self.stacked_layout)
        self.setCentralWidget(widget)
        self.show()

    def init_wnd_0(self):
        """Метод создает окно для показа рейтинга товара.
        :return: виджет окна."""

        form = qt.QFormLayout()
        # Выпадающий список с названиями товаров
        self.wnd_0_products = qt.QComboBox()
        self.wnd_0_products.setStyleSheet('background-color: white;')
        self.wnd_0_products.currentIndexChanged.connect(self.change_combobox)
        form.addRow('Товар', self.wnd_0_products)
        # Выпадающий список с фильтрами
        self.wnd_0_filters = qt.QComboBox()
        self.wnd_0_filters.setStyleSheet('background-color: white;')
        self.wnd_0_filters.currentIndexChanged.connect(self.change_combobox)
        form.addRow('Фильтр', self.wnd_0_filters)
        # Тип сортировки
        self.wnd_0_sorting = qt.QComboBox()
        self.wnd_0_sorting.setStyleSheet('background-color: white;')
        self.wnd_0_sorting.addItems(['По возрастанию', 'По убыванию'])
        self.wnd_0_sorting.currentIndexChanged.connect(self.sort)
        form.addRow('Сотировать', self.wnd_0_sorting)
        # Помещаем в группу
        group = qt.QGroupBox('Выберите товар и фильтр')
        group.setLayout(form)
        # Добавляем таблицу
        self.wnd_0_tbl = qt.QTableWidget()
        self.wnd_0_tbl.setColumnCount(3)
        self.wnd_0_tbl.setRowCount(0)
        self.wnd_0_tbl.setStyleSheet('background-color: white;')
        self.wnd_0_tbl.setHorizontalHeaderLabels(['Адрес', 'Дата', 'Оценка'])
        for i in range(3):
            self.wnd_0_tbl.horizontalHeader().setSectionResizeMode(
                i, qt.QHeaderView.Stretch)

        hbox = qt.QHBoxLayout()
        hbox.addWidget(group, alignment=Qt.AlignLeft)
        hbox.addWidget(self.wnd_0_tbl, 1)

        widget = qt.QWidget()
        widget.setLayout(hbox)
        return widget

    def init_wnd_1(self):
        """Метод создает окно для оценивания товара.
        :return: виджет окна."""

        form = qt.QFormLayout()
        # Выпадающий список с названиями товаров
        self.wnd_1_products = qt.QComboBox()
        self.wnd_1_products.setStyleSheet('background-color: white;')
        self.wnd_1_products.currentIndexChanged.connect(self.change_combobox)
        form.addRow('Товар', self.wnd_1_products)
        # Выпадающий список с фильтрами
        self.wnd_1_filters = qt.QComboBox()
        self.wnd_1_filters.setStyleSheet('background-color: white;')
        self.wnd_1_filters.currentIndexChanged.connect(self.change_combobox)
        form.addRow('Фильтр', self.wnd_1_filters)
        # Адрес
        self.wnd_1_address = qt.QLineEdit()
        self.wnd_1_address.setStyleSheet('background-color: white;')
        form.addRow('Адрес', self.wnd_1_address)
        # Оценка
        self.wnd_1_rating = qt.QLineEdit()
        self.wnd_1_rating.setStyleSheet('background-color: white;')
        validator = QRegExpValidator(QRegExp('^[-]?\d+\.?\d*'), self)
        self.wnd_1_rating.setValidator(validator)
        self.wnd_1_rating.textChanged.connect(self.check_rating)
        form.addRow('Оценка', self.wnd_1_rating)
        # Кнопка Оценить
        self.btn = qt.QPushButton('Оценить')
        self.btn.clicked.connect(self.estimate)
        self.btn.setEnabled(False)
        form.addWidget(self.btn)
        # Помещаем в группу
        group = qt.QGroupBox('Оцените товар')
        group.setLayout(form)
        # Добавляем таблицу
        self.wnd_1_tbl = qt.QTableWidget()
        self.wnd_1_tbl.setColumnCount(3)
        self.wnd_1_tbl.setRowCount(0)
        self.wnd_1_tbl.setStyleSheet('background-color: white;')
        self.wnd_1_tbl.setHorizontalHeaderLabels(['Адрес', 'Дата', 'Оценка'])
        for i in range(3):
            self.wnd_1_tbl.horizontalHeader().setSectionResizeMode(
                i, qt.QHeaderView.Stretch)

        hbox = qt.QHBoxLayout()
        hbox.addWidget(group, alignment=Qt.AlignLeft)
        hbox.addWidget(self.wnd_1_tbl, 1)

        widget = qt.QWidget()
        widget.setLayout(hbox)
        return widget

    def process_add_filter_or_product(self, msg):
        """Метод обрабатывает ответ на добавление фильтра или товара.
        :param msg: сообщение из сервера."""

        if msg.get(cn.STATUS) != 200:
            # Фильтр или товар не был добавлен
            info = 'Фильтр' if msg[cn.ACTION] == cn.ADD_FILTER else 'Товар'
            qt.QMessageBox.about(self, 'Информация', f'{info} не добавлен')
            return
        if msg[cn.ACTION] == cn.ADD_FILTER:
            render = self.render_filters
            array = self.filters
        else:
            render = self.render_products
            array = self.products
        # Добавляем в контейнер и перерисовываем
        array.append(msg.get(cn.CONTENT))
        render()

    def process_add_rating(self, msg):
        """Метод обрабатывает ответ на добавление оценки товара.
        :param msg: сообщение из сервера."""

        if msg.get(cn.STATUS) != 200:
            # Оценка не была добавлена
            qt.QMessageBox.about(self, 'Информация', f'Оценка не сохранена')
            return
        self.ratings = msg.get(cn.CONTENT)
        self.render_ratings(self.wnd_1_tbl, self.ratings)

    def process_data(self, msg):
        """Метод обрабатывает сообщения, пришедшие из сервера.
        :param msg: сообщение из сервера."""

        action = msg.get(cn.ACTION)
        if action == cn.ADD_FILTER or action == cn.ADD_PRODUCT:
            # Обрабатываем ответ на добавление фильтра или товара
            return self.process_add_filter_or_product(msg)
        if action == cn.ADD_RATING:
            # Обрабатываем ответ на добавление оценки
            return self.process_add_rating(msg)
        if action == cn.GET_FILTERS_AND_PRODUCTS:
            # Обрабатываем ответ на получение фильтров и товаров
            return self.process_get_filters_and_products(msg)
        if action == cn.GET_RATINGS:
            # Обрабатываем ответ на получение рейтинга товара
            return self.process_get_ratings(msg)

    def process_get_filters_and_products(self, msg):
        """Метод обрабатывает ответ на получение фильтров и товаров.
        :param msg: сообщение из сервера."""

        if msg.get(cn.STATUS) != 200:
            return
        # Запрос обработан
        content = msg.get(cn.CONTENT, {})
        self.filters = content.get(cn.FILTER)
        self.products = content.get(cn.PRODUCT)
        self.render_filters()
        self.render_products()

    def process_get_ratings(self, msg):
        """Метод обрабатывает ответ на получение рейтинга товара.
        :param msg: сообщение из сервера."""

        if msg.get(cn.STATUS) != 200:
            self.wnd_0_tbl.setRowCount(0)
            self.ratings = []
            return
        # Запрос обработан
        self.ratings = msg.get(cn.CONTENT)
        self.sort()

    def render_filters(self):
        """Метод перерисовывает выпадающие списки с фильтрами."""

        items = [filter[cn.FILTER] for filter in self.filters]
        # Выпадающий список на странице показа рейтинга товара
        self.wnd_0_filters.clear()
        self.wnd_0_filters.addItems(items)
        # Выпадающий список на странице оценивания товара
        self.wnd_1_filters.clear()
        self.wnd_1_filters.addItems(items)
        self.wnd_1_filters.addItem('Другой')

    def render_products(self):
        """Метод перерисовывает выпадающие списки с товарами."""

        items = [product[cn.PRODUCT] for product in self.products]
        # Выпадающий список на странице показа рейтинга товара
        self.wnd_0_products.clear()
        self.wnd_0_products.addItems(items)
        # Выпадающий список на странице оценивания товара
        self.wnd_1_products.clear()
        self.wnd_1_products.addItems(items)
        self.wnd_1_products.addItem('Другой')

    def render_ratings(self, tbl, data):
        """Метод перерисовывает таблицы с оценками.
        :patam tbl: таблица;
        :param data: данные, которые нужно отобразить в таблице."""

        tbl.setRowCount(len(data))
        for row, item in enumerate(data):
            tbl.setItem(row, 0, qt.QTableWidgetItem(item[cn.ADDRESS]))
            tbl.setItem(row, 1, qt.QTableWidgetItem(item[cn.DATE]))
            tbl.setItem(row, 2, qt.QTableWidgetItem(str(item[cn.RATING])))

    def set_to_default(self):
        """Метод задает всем атрибутам исходные значения."""

        # Список с фильтрами
        self.filters = []
        # Список с товарами
        self.products = []
        # Список с оценками
        self.ratings = []

    def show_info(self):
        """Метод выводит окно с краткой информацией о программе."""

        info = ('Программа для оценки стоимости и качества товаров\n'
                'Автор: Павел')
        qt.QMessageBox.about(self, 'Информация', info)

    def sort(self):
        """Метод сортирует рейтинг по возрастанию или убыванию."""

        if self.wnd_0_sorting.currentText() == 'По возрастанию':
            reverse = False
            data = self.ratings
        else:
            data = sorted(
                self.ratings, key=lambda x: x[cn.RATING], reverse=True)
        self.render_ratings(self.wnd_0_tbl, data)

    def switch_wnd(self):
        """Метод переключает окно при выборе пунктов меню 'Показать рейтинг
        товара' или 'Добавить оценку товару'."""

        if (self.sender().text() == 'Показать рейтинг' and
                self.stacked_layout.currentIndex() != 0):
            # Переключаем на окно с рейтингом
            self.stacked_layout.setCurrentIndex(0)
        elif (self.sender().text() == 'Оценить' and
                self.stacked_layout.currentIndex() != 1):
            # Запрашиваем фильтры и товары
            self.signal_to_send.emit({cn.ACTION: cn.GET_FILTERS_AND_PRODUCTS})
            # Переключаем на окно с оцениванием товара
            self.stacked_layout.setCurrentIndex(1)


if __name__ == '__main__':

    # Объект для чтения/отправки сообщений
    client = Client()
    client.connect()
    # Графическое окно
    app = qt.QApplication(sys.argv)
    w = Window(client)

    sys.exit(app.exec_())
