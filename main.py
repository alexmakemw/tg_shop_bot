from telebot import TeleBot, types
import re
import sqlite3
import json
from datetime import datetime

bot = TeleBot('ваш токен')
email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$')
ADMIN_ID = ваш_id

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Таблица категорий товаров
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT NOT NULL,
        parent_category_id INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    )
    ''')
    
    # Таблица товаров
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        product_name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        stock_quantity INTEGER DEFAULT 0,
        image_url TEXT,
        specifications TEXT,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
    )
    ''')
    
    # Таблица корзины
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cart (
        cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER DEFAULT 1,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    ''')
    
    # Таблица заказов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_amount REAL,
        status TEXT DEFAULT 'pending',
        shipping_address TEXT,
        contact_phone TEXT,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    # Таблица элементов заказа
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        price_per_unit REAL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    ''')
    
    conn.commit()
    
    # Добавляем тестовые данные если таблицы пустые
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        # Добавляем основные категории
        categories = [
            ('Дрели и шуруповерты', 0),
            ('Перфораторы', 0),
            ('Болгарки (УШМ)', 0),
            ('Электролобзики', 0),
            ('Шлифмашины', 0),
            ('Пылесосы строительные', 0),
            ('Отбойные молотки', 0),
            ('Расходные материалы', 0)
        ]
        cursor.executemany('INSERT INTO categories (category_name, parent_category_id) VALUES (?, ?)', categories)
        
        # Добавляем тестовые товары
        test_products = [
            (1, 'Дрель-шуруповерт Bosch GSR 120-LI', 'Аккумуляторная дрель-шуруповерт, 12В, 2 аккумулятора', 8999.99, 15, '{"power": "12V", "torque": "30Nm", "battery": "Li-Ion 2x2.0Ah"}'),
            (1, 'Дрель Makita HP1640', 'Сетевая дрель, 710Вт, патрон 13мм', 5499.50, 8, '{"power": "710W", "rpm": "0-2800", "chuck": "13mm"}'),
            (2, 'Перфоратор DeWalt D25601K', 'Перфоратор 900Вт, 3.2Дж, SDS-MAX', 18999.99, 5, '{"power": "900W", "impact_energy": "3.2J", "blows_per_minute": "1150"}'),
            (3, 'Болгарка Metabo W 750-125', 'УШМ 750Вт, диск 125мм, регулировка оборотов', 6999.99, 12, '{"power": "750W", "disc_diameter": "125mm", "rpm": "11000"}'),
            (4, 'Электролобзик Интерскол МП-100Э', 'Лобзик 600Вт, маятниковый ход, регулировка скорости', 3299.99, 20, '{"power": "600W", "stroke_rate": "500-3000spm", "stroke_length": "18mm"}'),
            (5, 'Шлифмашина вибрационная Bort BSM-300N', 'Площадь платформы 150х100мм, 300Вт, регулятор скорости', 2599.99, 18, '{"power": "300W", "plate_size": "150x100mm", "oscillations_per_minute": "12000-20000"}')
        ]
        cursor.executemany('INSERT INTO products (category_id, product_name, description, price, stock_quantity, specifications) VALUES (?, ?, ?, ?, ?, ?)', test_products)
        
        conn.commit()
    
    conn.close()

# Инициализация базы данных при запуске
init_db()

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С БД ==========
def get_db_connection():
    return sqlite3.connect('bot_database.db', check_same_thread=False)

def get_user_data(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(user_id, username, first_name, last_name, email, phone='', address=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (user_id, username, first_name, last_name, email, phone, address) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name, email, phone, address))
    conn.commit()
    conn.close()

def get_categories(parent_id=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT category_id, category_name FROM categories WHERE parent_category_id = ? AND is_active = 1', (parent_id,))
    categories = cursor.fetchall()
    conn.close()
    return categories

def get_products_by_category(category_id, limit=20):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT product_id, product_name, description, price, stock_quantity 
        FROM products 
        WHERE category_id = ? AND is_active = 1 
        LIMIT ?
    ''', (category_id, limit))
    products = cursor.fetchall()
    conn.close()
    return products

def get_product_details(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE product_id = ?', (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product

def add_to_cart(user_id, product_id, quantity=1):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем, есть ли уже такой товар в корзине
    cursor.execute('SELECT cart_id, quantity FROM cart WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    existing_item = cursor.fetchone()
    
    if existing_item:
        # Обновляем количество
        new_quantity = existing_item[1] + quantity
        cursor.execute('UPDATE cart SET quantity = ? WHERE cart_id = ?', (new_quantity, existing_item[0]))
    else:
        # Добавляем новый товар
        cursor.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)', (user_id, product_id, quantity))
    
    conn.commit()
    conn.close()

def get_cart_items(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.cart_id, p.product_id, p.product_name, p.price, c.quantity, p.stock_quantity
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = ?
    ''', (user_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def remove_from_cart(cart_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart WHERE cart_id = ?', (cart_id,))
    conn.commit()
    conn.close()

def clear_cart(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# ========== КОМАНДА START ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if not user:
        bot.send_message(message.chat.id, "Добро пожаловать в магазин электроинструментов!\n\nДля полного доступа к функциям магазина, пожалуйста, зарегистрируйтесь командой /reg")
    else:
        bot.send_message(message.chat.id, f"С возвращением, {user[2]}!")
    
    show_main_menu(message)

# ========== ПОКАЗ ГЛАВНОГО МЕНЮ ==========
def show_main_menu(message_or_chat_id, user_id=None):
    if isinstance(message_or_chat_id, types.Message):
        chat_id = message_or_chat_id.chat.id
        user_id = message_or_chat_id.from_user.id
    elif isinstance(message_or_chat_id, types.CallbackQuery):
        chat_id = message_or_chat_id.message.chat.id
        user_id = message_or_chat_id.from_user.id
    else:
        chat_id = message_or_chat_id
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    btn1 = types.KeyboardButton('Каталог')
    btn2 = types.KeyboardButton('Корзина')
    btn3 = types.KeyboardButton('Мои заказы')
    btn4 = types.KeyboardButton('О магазине')
    btn5 = types.KeyboardButton('Контакты')
    
    if user_id == ADMIN_ID:
        btn6 = types.KeyboardButton('⚙️ Админ-панель')
        markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    else:
        markup.add(btn1, btn2, btn3, btn4, btn5)
    
    bot.send_message(
        chat_id,
        'Главное меню\nВыберите нужный раздел:',
        reply_markup=markup
    )

# ========== КАТАЛОГ ==========
@bot.message_handler(func=lambda message: message.text == 'Каталог')
def show_catalog(message):
    categories = get_categories()
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for category_id, category_name in categories:
        markup.add(
            types.InlineKeyboardButton(
                category_name,
                callback_data=f'category_{category_id}'
            )
        )
    
    bot.send_message(
        message.chat.id,
        '**Каталог электроинструментов**\n\nВыберите категорию:',
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('category_'))
def show_category_products(call):
    category_id = int(call.data.split('_')[1])
    products = get_products_by_category(category_id)
    
    if not products:
        bot.answer_callback_query(call.id, "В этой категории пока нет товаров")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for product in products:
        product_id, product_name, _, price, stock = product
        stock_status = "В наличии" if stock > 0 else "Нет в наличии"
        
        markup.add(
            types.InlineKeyboardButton(
                f"{product_name} - {price}₽",
                callback_data=f'product_{product_id}'
            )
        )
    
    markup.add(
        types.InlineKeyboardButton(
            '⬅️ Назад к категориям',
            callback_data='back_to_categories'
        )
    )
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='**Товары в категории:**\n\nВыберите товар для просмотра подробностей:',
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
def show_product_details(call):
    product_id = int(call.data.split('_')[1])
    product = get_product_details(product_id)
    
    if not product:
        bot.answer_callback_query(call.id, "Товар не найден")
        return
    
    # Распаковываем данные товара
    _, category_id, name, description, price, stock, image, specs_json, _ = product
    
    try:
        specs = json.loads(specs_json) if specs_json else {}
        specs_text = "\n".join([f"• {k}: {v}" for k, v in specs.items()])
    except:
        specs_text = "Характеристики не указаны"
    
    stock_status = "✅ В наличии" if stock > 0 else "❌ Нет в наличии"
    
    # Исправлено: убираем разметку Markdown для предотвращения ошибок парсинга
    message_text = f"""
🔧 {name}

Цена: {price}₽
{stock_status} ({stock} шт.)

Описание:
{description}

Характеристики:
{specs_text}
"""
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if stock > 0:
        markup.add(
            types.InlineKeyboardButton(
                '➕ Добавить в корзину',
                callback_data=f'add_to_cart_{product_id}'
            )
        )
    
    markup.add(
        types.InlineKeyboardButton(
            '⬅️ Назад к товарам',
            callback_data=f'category_{category_id}'
        )
    )
    
    # Исправлено: убираем parse_mode='Markdown' или заменяем на 'HTML'
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=message_text,
        reply_markup=markup,
        parse_mode='HTML'  # Или полностью убрать parse_mode
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_to_cart_'))
def add_product_to_cart(call):
    user_id = call.from_user.id
    product_id = int(call.data.split('_')[3])
    
    # Проверяем, зарегистрирован ли пользователь
    user = get_user_data(user_id)
    if not user:
        bot.answer_callback_query(
            call.id,
            "Для добавления в корзину нужно зарегистрироваться! Используйте /reg",
            show_alert=True
        )
        return
    
    add_to_cart(user_id, product_id)
    bot.answer_callback_query(call.id, "✅ Товар добавлен в корзину!")

# ========== КОРЗИНА ==========
@bot.message_handler(func=lambda message: message.text == '🛒 Корзина')
def show_cart(message):
    user_id = message.from_user.id
    cart_items = get_cart_items(user_id)
    
    if not cart_items:
        bot.send_message(message.chat.id, "🛒 Ваша корзина пуста")
        return
    
    total = 0
    cart_text = "🛒 Ваша корзина:\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for item in cart_items:
        cart_id, product_id, name, price, quantity, stock = item
        item_total = price * quantity
        total += item_total
        
        cart_text += f"• {name}\n"
        cart_text += f"  Цена: {price}₽ × {quantity} = {item_total}₽\n"
        
        markup.add(
            types.InlineKeyboardButton(
                f"Удалить {name[:15]}...",
                callback_data=f'remove_from_cart_{cart_id}'
            )
        )
    
    cart_text += f"\n Итого: {total}₽"
    
    markup.add(
        types.InlineKeyboardButton(
            'Очистить корзину',
            callback_data='clear_cart'
        ),
        types.InlineKeyboardButton(
            'Оформить заказ',
            callback_data='checkout'
        )
    )
    
    markup.add(
        types.InlineKeyboardButton(
            '⬅️ Вернуться в меню',
            callback_data='back_to_menu'
        )
    )
    
    bot.send_message(
        message.chat.id,
        cart_text,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('remove_from_cart_'))
def remove_item_from_cart(call):
    cart_id = int(call.data.split('_')[3])
    remove_from_cart(cart_id)
    
    bot.answer_callback_query(call.id, "Товар удален из корзины")
    
    # Обновляем корзину
    user_id = call.from_user.id
    cart_items = get_cart_items(user_id)
    
    if not cart_items:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🛒 Ваша корзина пуста",
            reply_markup=None
        )
        return
    
    total = 0
    cart_text = "🛒 Ваша корзина:\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for item in cart_items:
        cart_id, product_id, name, price, quantity, stock = item
        item_total = price * quantity
        total += item_total
        
        cart_text += f"• {name}\n"
        cart_text += f"  Цена: {price}₽ × {quantity} = {item_total}₽\n"
        
        markup.add(
            types.InlineKeyboardButton(
                f"Удалить {name[:15]}...",
                callback_data=f'remove_from_cart_{cart_id}'
            )
        )
    
    cart_text += f"\n Итого: {total}₽"
    
    markup.add(
        types.InlineKeyboardButton(
            '🔄 Очистить корзину',
            callback_data='clear_cart'
        ),
        types.InlineKeyboardButton(
            '💳 Оформить заказ',
            callback_data='checkout'
        )
    )
    
    markup.add(
        types.InlineKeyboardButton(
            '⬅️ Вернуться в меню',
            callback_data='back_to_menu'
        )
    )
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=cart_text,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'clear_cart')
def clear_user_cart(call):
    user_id = call.from_user.id
    clear_cart(user_id)
    
    bot.answer_callback_query(call.id, "Корзина очищена")
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🛒 Ваша корзина пуста"
    )

# РЕГИСТРАЦИЯ
@bot.message_handler(commands=['reg'])
def reg(message):
    user_id = message.from_user.id
    existing_user = get_user_data(user_id)
    
    if existing_user:
        bot.send_message(message.chat.id, f"Вы уже зарегистрированы!\n\nИмя: {existing_user[2]}\nEmail: {existing_user[4]}")
        return
    
    bot.send_message(message.chat.id, "Регистрация в магазине\n\nКак вас зовут?")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, "Введите вашу фамилию:")
    bot.register_next_step_handler(message, lambda msg: get_surname(msg, message.text))

def get_surname(message, first_name):
    user_id = message.from_user.id
    last_name = message.text
    bot.send_message(message.chat.id, "Введите ваш email:")
    bot.register_next_step_handler(message, lambda msg: get_email(msg, first_name, last_name))

def get_email(message, first_name, last_name):
    user_id = message.from_user.id
    email = message.text
    
    if not email_pattern.match(email):
        bot.send_message(message.chat.id, '❌ Некорректный email. Пожалуйста, введите корректный адрес:')
        bot.register_next_step_handler(message, lambda msg: get_email(msg, first_name, last_name))
        return
    
    keyboard = types.InlineKeyboardMarkup()
    key_yes = types.InlineKeyboardButton(text='✅ Да, все верно', callback_data=f'confirm_reg_{first_name}_{last_name}_{email}')
    key_no = types.InlineKeyboardButton(text='❌ Нет, исправить', callback_data='cancel_reg')
    keyboard.add(key_yes, key_no)
    
    question = f"""
Проверьте данные:

Имя: {first_name}
Фамилия: {last_name}
Email: {email}

Всё верно?
"""
    bot.send_message(message.chat.id, text=question, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_reg_'))
def confirm_registration(call):
    data_parts = call.data.split('_')
    first_name = data_parts[2]
    last_name = data_parts[3]
    email = data_parts[4]
    
    user_id = call.from_user.id
    username = call.from_user.username
    
    # Сохраняем пользователя в БД
    register_user(user_id, username, first_name, last_name, email)
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"Регистрация завершена!\n\nДобро пожаловать в магазин, {first_name}!",
        reply_markup=None
    )
    
    show_main_menu(call)

# АДМИН-ПАНЕЛЬ
@bot.message_handler(func=lambda message: message.text == '⚙️ Админ-панель' and message.from_user.id == ADMIN_ID)
def admin_panel(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    markup.add(
        types.InlineKeyboardButton('Статистика', callback_data='admin_stats'),
        types.InlineKeyboardButton('Управление товарами', callback_data='admin_products'),
        types.InlineKeyboardButton('Пользователи', callback_data='admin_users'),
        types.InlineKeyboardButton('Заказы', callback_data='admin_orders')
    )
    
    bot.send_message(
        message.chat.id,
        "⚙️ Админ-панель\n\nВыберите раздел:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'admin_stats')
def show_admin_stats(call):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Получаем статистику
    cursor.execute('SELECT COUNT(*) FROM users')
    users_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM products')
    products_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM orders')
    orders_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(total_amount) FROM orders WHERE status = "completed"')
    total_revenue = cursor.fetchone()[0] or 0
    
    conn.close()
    
    stats_text = f"""
Статистика магазина:

Пользователей: {users_count}
Товаров: {products_count}
Заказов: {orders_count}
Общая выручка: {total_revenue}₽
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='back_to_admin'))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=stats_text,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'admin_products')
def show_admin_products(call):
    """Управление товарами - в разработке"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='back_to_admin'))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Управление товарами\n\n Находится в разработке",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'admin_users')
def show_admin_users(call):
    """Управление пользователями - в разработке"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='back_to_admin'))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Пользователи\n\nНаходится в разработке",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'admin_orders')
def show_admin_orders(call):
    """Управление заказами - в разработке"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='back_to_admin'))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Заказы\n\nНаходится в разработке",
        reply_markup=markup
    )

# ОБРАБОТКА CALLBACK 
@bot.callback_query_handler(func=lambda call: call.data == 'back_to_categories')
def back_to_categories(call):
    """Возврат к списку категорий"""
    categories = get_categories()
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for category_id, category_name in categories:
        markup.add(
            types.InlineKeyboardButton(
                category_name,
                callback_data=f'category_{category_id}'
            )
        )
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Каталог электроинструментов\n\nВыберите категорию:',
            reply_markup=markup
        )
    except Exception as e:
        print(f"Ошибка при редактировании сообщения: {e}")
        # Если не удалось отредактировать, отправляем новое сообщение
        bot.send_message(
            call.message.chat.id,
            '🔧 Каталог электроинструментов\n\nВыберите категорию:',
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_menu')
def back_to_main_menu(call):
    """Возврат в главное меню"""
    try:
        # Удаляем сообщение с кнопками
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    # Показываем главное меню
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    btn1 = types.KeyboardButton('Каталог')
    btn2 = types.KeyboardButton('Корзина')
    btn3 = types.KeyboardButton('Мои заказы')
    btn4 = types.KeyboardButton('О магазине')
    btn5 = types.KeyboardButton('Контакты')
    
    if call.from_user.id == ADMIN_ID:
        btn6 = types.KeyboardButton('⚙️ Админ-панель')
        markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    else:
        markup.add(btn1, btn2, btn3, btn4, btn5)
    
    bot.send_message(
        call.message.chat.id,
        'Главное меню\nВыберите нужный раздел:',
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_admin')
def back_to_admin(call):
    """Возврат в админ-панель"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    markup.add(
        types.InlineKeyboardButton('Статистика', callback_data='admin_stats'),
        types.InlineKeyboardButton('Управление товарами', callback_data='admin_products'),
        types.InlineKeyboardButton('Пользователи', callback_data='admin_users'),
        types.InlineKeyboardButton('Заказы', callback_data='admin_orders')
    )
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="⚙️ Админ-панель\n\nВыберите раздел:",
            reply_markup=markup
        )
    except:
        bot.send_message(
            call.message.chat.id,
            "⚙️ Админ-панель\n\nВыберите раздел:",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_reg')
def cancel_registration(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Регистрация отменена. Для начала заново используйте /reg"
    )

@bot.callback_query_handler(func=lambda call: call.data == 'checkout')
def checkout(call):
    """Оформление заказа"""
    bot.answer_callback_query(call.id, "Функция оформления заказа в разработке")

# ДРУГИЕ РАЗДЕЛЫ
@bot.message_handler(func=lambda message: message.text == '📦 Мои заказы')
def my_orders(message):
    bot.send_message(message.chat.id, "📋 Мои заказы\n\nРаздел в разработке...")

@bot.message_handler(func=lambda message: message.text == 'ℹ️ О магазине')
def about(message):
    about_text = """
🏪 О нашем магазине

Мы специализируемся на продаже профессионального электроинструмента уже более 10 лет!

Наши преимущества:
• Только оригинальная продукция
• Гарантия на все товары
• Бесплатная доставка от 5000₽
• Консультация специалистов

Ассортимент:
• Электроинструменты
• Садовая техника
• Расходные материалы
• Запчасти и комплектующие

Режим работы:
Пн-Пт: 9:00-20:00
Сб-Вс: 10:00-18:00
"""
    bot.send_message(message.chat.id, about_text)

@bot.message_handler(func=lambda message: message.text == '📞 Контакты')
def contacts(message):
    contacts_text = """
Контакты

Адрес:
г. Москва, ул. Инструментальная, д. 15

Телефоны:
+7 (495) 123-45-67 - Отдел продаж
+7 (495) 123-45-68 - Сервисный центр

Email:
info@electrotools.ru
support@electrotools.ru

Сайт:
www.electrotools.ru

Социальные сети:
@electrotools_shop - Telegram
electrotools - Instagram
"""
    bot.send_message(message.chat.id, contacts_text)

# ЗАПУСК БОТА 
if __name__ == '__main__':
    print("Бот магазина электроинструментов запущен...")
    print("База данных инициализирована")
    print("Админ ID:", ADMIN_ID)
    bot.polling(none_stop=True, interval=0)
