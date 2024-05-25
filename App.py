import jwt
import datetime
import secrets
from functools import wraps
from flask import Flask, request, jsonify
import sqlite3
from flask import Flask, render_template, jsonify, request
import requests

app = Flask(__name__)

# تولید کلید مخفی یکبار در هنگام اجرا
SECRET_KEY = secrets.token_hex(16)

# تابع برای ایجاد اتصال به دیتابیس SQLite
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# تابع برای ایجاد جدول کاربران در دیتابیس
def create_users_table():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (username TEXT PRIMARY KEY, first_name TEXT, last_name TEXT, age INTEGER, phone_number TEXT)''')

# تابع  برای ایجاد جدول توکن‌ها در دیتابیس
def create_tokens_table():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS tokens
                     (username TEXT PRIMARY KEY, token TEXT)''')

# تابع  برای ایجاد جدول رمزهای عبور در دیتابیس
def create_passwords_table():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS passwords
                     (username TEXT PRIMARY KEY, password TEXT)''')
        
# تابع برای ایجاد جدول ولت‌ها در دیتابیس
def create_wallets_table():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS wallets
                     (username TEXT, balance INTEGER, currency TEXT, description TEXT, status TEXT, created_at TIMESTAMP, last_updated_at TIMESTAMP, wallet_type TEXT)''')


# تابع برای ایجاد همه جدول‌ها
def create_database_tables():
    create_users_table()
    create_tokens_table()
    create_passwords_table()
    create_wallets_table()


# فراخوانی تابع برای ایجاد جدول‌ها
create_database_tables()
create_wallets_table()


# دست‌رسی به توکن JWT
def generate_token(username):
    payload = {
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)  # توکن در 30 دقیقه انقضا می‌شود
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

# دکوراتور برای نیاز به احراز هویت توکن برای برخی از روت‌ها
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        token_parts = token.split(' ')
        if len(token_parts) != 2 or token_parts[0].lower() != 'bearer':
            return jsonify({'message': 'Invalid token format!'}), 401

        try:
            data = jwt.decode(token_parts[1], SECRET_KEY, algorithms=['HS256'])
            username = data['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(username, *args, **kwargs)

    return decorated

# روت برای دسترسی نیاز به توکن احراز هویت دارد
@app.route('/protected')
@token_required
def protected(username):
    return jsonify({'message': f'Hello, {username}! This is a protected endpoint.'})

# روت لاگین برای تولید توکن در صورت لاگین موفقیت‌آمیز
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT password FROM passwords WHERE username=?", (username,))
        user = c.fetchone()

    if user and user[0] == password:
        token = generate_token(username)
        
        # ذخیره توکن در جدول توکن‌ها
        with get_db_connection() as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO tokens (username, token) VALUES (?, ?)", (username, token))
                conn.commit()
            except sqlite3.IntegrityError:
                c.execute("UPDATE tokens SET token=? WHERE username=?", (token, username))
                conn.commit()
        
        return jsonify({'token': token})

    return jsonify({'message': 'Invalid username/password!'}), 401

# روت برای ثبت نام کاربر جدید
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    age = data.get('age')
    phone_number = data.get('phone_number')

    if username and password:
        with get_db_connection() as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, first_name, last_name, age, phone_number) VALUES (?, ?, ?, ?, ?)", (username, first_name, last_name, age, phone_number))
                # ذخیره پسورد در جدول پسوردها
                c.execute("INSERT INTO passwords (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                return jsonify({'message': 'Registration successful!'})
            except sqlite3.IntegrityError:
                return jsonify({'message': 'Username already exists!'}), 400
    else:
        return jsonify({'message': 'Missing username or password!'}), 400

# روت برای ثبت کاربر جدید
@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    age = data.get('age')
    phone_number = data.get('phone_number')

    if username and password:
        with get_db_connection() as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, first_name, last_name, age, phone_number) VALUES (?, ?, ?, ?, ?)", (username, first_name, last_name, age, phone_number))
                # ذخیره پسورد در جدول پسوردها
                c.execute("INSERT INTO passwords (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                return jsonify({'message': 'User added successfully!'})
            except sqlite3.IntegrityError:
                return jsonify({'message': 'Username already exists!'}), 400
    else:
        return jsonify({'message': 'Missing username or password!'}), 400

# روت برای حذف حساب کاربری
@app.route('/delete_account', methods=['POST'])
@token_required
def delete_account(username):
    data = request.json
    password = data.get('password')

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT password FROM passwords WHERE username=?", (username,))
        user = c.fetchone()

        if user and user[0] == password:
            c.execute("DELETE FROM users WHERE username=?", (username,))
            c.execute("DELETE FROM tokens WHERE username=?", (username,))
            c.execute("DELETE FROM passwords WHERE username=?", (username,))
            conn.commit()
            return jsonify({'message': 'Account deleted successfully!'})
        else:
            return jsonify({'message': 'Invalid password!'}), 401

# روت برای ویرایش اطلاعات کاربری
@app.route('/edit_user', methods=['POST'])
@token_required
def edit_user(username):
    data = request.json
    new_username = data.get('new_username')
    new_password = data.get('new_password')
    current_password = data.get('current_password')  # اضافه کردن فیلد current_password

    if new_username or new_password:
        with get_db_connection() as conn:
            c = conn.cursor()
            # اعتبارسنجی پسورد فعلی کاربر
            c.execute("SELECT password FROM passwords WHERE username=?", (username,))
            current_password_row = c.fetchone()

            if current_password_row and current_password_row[0] == current_password:
                try:
                    if new_username:
                        c.execute("UPDATE users SET username=? WHERE username=?", (new_username, username))
                        c.execute("UPDATE tokens SET username=? WHERE username=?", (new_username, username))
                    if new_password:
                        c.execute("UPDATE passwords SET username=?, password=? WHERE username=?", (new_username, new_password, username))

                    conn.commit()
                    return jsonify({'message': 'User information updated successfully!'})
                except sqlite3.IntegrityError:
                    return jsonify({'message': 'Username already exists!'}), 400
            else:
                return jsonify({'message': 'Invalid current password!'}), 401
    else:
        return jsonify({'message': 'No new information provided!'}), 400

# روت برای ویرایش اطلاعات کاربران
@app.route('/edit_user_info', methods=['POST'])
@token_required
def edit_user_info(username):
    data = request.json
    new_first_name = data.get('new_first_name')
    new_last_name = data.get('new_last_name')
    new_age = data.get('new_age')
    new_phone_number = data.get('new_phone_number')
    new_password = data.get('new_password')
    current_password = data.get('current_password')
    new_username = data.get('new_username')

    if new_first_name or new_last_name or new_age or new_phone_number or new_password:  # اصلاح شرط برای بررسی وجود اطلاعات جدید
        with get_db_connection() as conn:
            c = conn.cursor()
            # اعتبارسنجی پسورد فعلی کاربر و بازیابی پسورد از جدول پسوردها
            c.execute("SELECT password FROM passwords WHERE username=?", (username,))
            user_password = c.fetchone()

            if user_password and user_password[0] == current_password:
                try:
                    if new_first_name:
                        c.execute("UPDATE users SET first_name=? WHERE username=?", (new_first_name, username))
                    if new_last_name:
                        c.execute("UPDATE users SET last_name=? WHERE username=?", (new_last_name, username))
                    if new_age:
                        c.execute("UPDATE users SET age=? WHERE username=?", (new_age, username))
                    if new_phone_number:
                        c.execute("UPDATE users SET phone_number=? WHERE username=?", (new_phone_number, username))

                    # به‌روزرسانی پسورد و یوزرنیم در جدول پسوردها
                    if new_password:
                        c.execute("UPDATE passwords SET username=?, password=? WHERE username=?", (new_username, new_password, username))

                    # بروزرسانی یوزرنیم در جدول کاربران
                    if new_username:
                        c.execute("UPDATE users SET username=? WHERE username=?", (new_username, username))
                        c.execute("UPDATE tokens SET username=? WHERE username=?", (new_username, username))

                    conn.commit()
                    return jsonify({'message': 'User information updated successfully!'})
                except sqlite3.Error as e:
                    return jsonify({'message': 'An error occurred while updating user information.', 'error': str(e)}), 500
            else:
                return jsonify({'message': 'Invalid current password!'}), 401
    else:
        return jsonify({'message': 'No new information provided!'}), 400

# روت برای نمایش توکن‌های همه کاربران
@app.route('/user_tokens')
def user_tokens():
    user_tokens = get_user_tokens()
    return jsonify({'user_tokens': user_tokens})

# روت برای افزودن ولت به حساب کاربری
@app.route('/add_wallet', methods=['POST'])
@token_required
def add_wallet(username):
    data = request.json
    balance = data.get('balance')
    wallet_type = data.get('wallet_type')  # اضافه کردن نوع ولت
    currency = data.get('currency')  # اضافه کردن واحد پول
    description = data.get('description')  # اضافه کردن توضیحات
    status = data.get('status')  # اضافه کردن وضعیت فعلی
    created_at = datetime.datetime.now()  # اضافه کردن تاریخ ایجاد به زمان فعلی
    last_updated_at = created_at  # اضافه کردن زمان اخرین بروزرسانی به زمان فعلی

    if balance is not None and isinstance(balance, int) and balance >= 0:
        with get_db_connection() as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO wallets (username, balance, wallet_type, currency, description, status, created_at, last_updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (username, balance, wallet_type, currency, description, status, created_at, last_updated_at))
                conn.commit()
                return jsonify({'message': 'Wallet added successfully!'})
            except sqlite3.IntegrityError:
                return jsonify({'message': 'Wallet already exists for this user!'}), 400
    else:
        return jsonify({'message': 'Invalid balance provided!'}), 400
    

# روت برای حذف ولت
@app.route('/delete_wallet', methods=['POST'])
@token_required
def delete_wallet(username):
    data = request.json
    password = data.get('password')
    username = data.get('username')

    if not authenticate_user(username, password):
        return jsonify({'message': 'Authentication failed!'}), 401

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM passwords WHERE username=?", (username,))
        wallet = c.fetchone()

        if wallet:
            try:
                c.execute("DELETE FROM wallets WHERE username=?", (username,))
                conn.commit()
                return jsonify({'message': 'Wallet deleted successfully!'})
            except sqlite3.Error as e:
                return jsonify({'message': 'Failed to delete wallet.', 'error': str(e)}), 500
        else:
            return jsonify({'message': 'Wallet not found or you do not have permission to delete it!'}), 404

# روت برای ویرایش ولت
@app.route('/edit_wallet', methods=['POST'])
@token_required
def edit_wallet(username):
    data = request.json
    balance = data.get('balance')
    wallet_type = data.get('wallet_type')
    currency = data.get('currency')
    description = data.get('description')
    status = data.get('status')
    last_updated_at = datetime.datetime.now()

    if data or balance or wallet_type or currency or description or status :  # اصلاح شرط برای بررسی وجود اطلاعات جدید
      with get_db_connection() as conn:
          c = conn.cursor()
          c.execute("SELECT * FROM wallets WHERE username=?", (username,))
          wallet = c.fetchone()

          if wallet:
              try:
                  c.execute("UPDATE wallets SET balance=?, wallet_type=?, currency=?, description=?, status=?, last_updated_at=? WHERE username=?", (balance, wallet_type, currency, description, status, last_updated_at, username))
                  conn.commit()
                  return jsonify({'message': 'Wallet updated successfully!'})
              except sqlite3.Error as e:
                  return jsonify({'message': 'Failed to update wallet.', 'error': str(e)}), 500
          else:
              return jsonify({'message': 'Wallet not found or you do not have permission to edit it!'}), 404

#تابع برای احراز کاربران از طریق یوزر و پسورد 
def authenticate_user(username, password):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT password FROM passwords WHERE username=?", (username,))
        fetched_password = c.fetchone()

        if fetched_password and password == fetched_password[0]:
            return True
        else:
            return False


# تابع برای بازیابی توکن‌های همه کاربران از دیتابیس
def get_user_tokens():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, token FROM tokens")
    tokens = cursor.fetchall()
    conn.close()
    return tokens

if __name__ == '__main__':
    app.run(debug=True)
