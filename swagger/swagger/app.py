from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from flask_swagger_ui import get_swaggerui_blueprint
import json
import datetime
import jwt
from functools import wraps
import secrets
import sqlite3
from flask.views import MethodView

# تولید کلید مخفی یکبار در هنگام اجرا
class SecretKeyGenerator:
    def __init__(self):
        self._secret_key = None

    @property
    def secret_key(self):
        if not self._secret_key:
            self._secret_key = secrets.token_hex(16)
        return self._secret_key

SECRET_KEY = SecretKeyGenerator().secret_key


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
api = Api(app)

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

# تابع برای ایجاد جدول توکن‌ها در دیتابیس
def create_tokens_table():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS tokens
                     (username TEXT PRIMARY KEY, token TEXT)''')

# تابع برای ایجاد جدول رمزهای عبور در دیتابیس
def create_passwords_table():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS passwords
                     (username TEXT PRIMARY KEY, password TEXT)''')

# تابع برای ایجاد همه جدول‌ها
def create_database_tables():
    create_users_table()
    create_tokens_table()
    create_passwords_table()

# فراخوانی تابع برای ایجاد جدول‌ها
create_database_tables()

#دسترسی به توکن JWT
class JWTTokenGenerator:
    def __init__(self, secret_key):
        self.secret_key = secret_key

    def generate_token(self, username):
        payload = {
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)  # توکن در 30 دقیقه انقضا می‌شود
        }
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token

# دکوراتور برای نیاز به احراز هویت توکن برای برخی از روت‌ها
class token_required:
    def __init__(self, f):
        self.f = f

    def __call__(self, *args, **kwargs):
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

        return self.f(username, *args, **kwargs)


# Define a sample resource
class HelloWorld(Resource):
    def get(self):
        return jsonify({'message': 'Hello, World!'})

# Define a User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.name}>'

## کلاس برای Protected
#class Protected(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    name = db.Column(db.String(50), nullable=False)
#    email = db.Column(db.String(120), unique=True, nullable=False)

#    def __repr__(self):
#        return f'<Protected {self.name}>'

# روت برای دسترسی نیاز به توکن احراز هویت دارد
#class Protected(Resource):
#    def get(self):
#        users = Protected.query.all()
#        user_list = [{'id': user.id, 'name': user.name, 'email': user.email} for user in users]
#        return jsonify(Protected)


# کلاس برای Protected
class Protected(Resource):
    # دکوراتور برای نیاز به احراز هویت توکن برای دسترسی به روت
    @staticmethod
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
    
    @token_required
    def get(self, username):
        # درخواست همه‌ی کاربران از دیتابیس
        users = User.query.all()
        
        # تبدیل کاربران به فرمت JSON
        user_list = [{'id': user.id, 'name': user.name, 'email': user.email} for user in users]
        
        # برگرداندن JSON به عنوان پاسخ
        return jsonify(user_list)

# کلاس روت لاگین برای تولید توکن در صورت لاگین موفقیت‌آمیز
class Login(Resource):
    def post(self):
        data = request.json
        username = data.get('username')
        password = data.get('password')

        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT password FROM passwords WHERE username=?", (username,))
            user = c.fetchone()

        if user and user[0] == password:
            token = JWTTokenGenerator(SECRET_KEY).generate_token(username)
            
            # ذخیره توکن در جدول توکن‌ها
            with get_db_connection() as conn:
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO tokens (username, token) VALUES (?, ?)", (username, token))
                    conn.commit()
                except sqlite3.IntegrityError:
                    c.execute("UPDATE tokens SET token=? WHERE username=?", (token, username))
                    conn.commit()
            
            return {'token': token}, 200

        return {'message': 'Invalid username/password!'}, 401

# روت برای ثبت نام کاربر جدید Register 
class Register(Resource):
    def post(self):
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
                    return {'message': 'Registration successful!'}, 200
                except sqlite3.IntegrityError:
                    return {'message': 'Username already exists!'}, 400
        else:
            return {'message': 'Missing username or password!'}, 400



# روت برای ثبت کاربر جدید Add_User
class AddUser(MethodView):
    def post(self):
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
class DeleteAccount(Resource):
    @staticmethod
    @token_required
    def post(username):
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
class EditUser(Resource):
    @staticmethod
    @token_required
    def post(username):
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
                            c.execute("UPDATE passwords SET password=? WHERE username=?", (new_password, username))

                        conn.commit()
                        return jsonify({'message': 'User information updated successfully!'})
                    except sqlite3.IntegrityError:
                        return jsonify({'message': 'Username already exists!'}), 400
                else:
                    return jsonify({'message': 'Invalid current password!'}), 401
        else:
            return jsonify({'message': 'No new information provided!'}), 400


# روت برای ویرایش اطلاعات کاربری کامل
class EditUserInfo(Resource):
    @token_required
    def post(self, username):
        data = request.json
        new_first_name = data.get('new_first_name')
        new_last_name = data.get('new_last_name')
        new_age = data.get('new_age')
        new_phone_number = data.get('new_phone_number')
        new_password = data.get('new_password')
        current_password = data.get('current_password')
        new_username = data.get('new_username')

        if new_first_name or new_last_name or new_age or new_phone_number or new_password:  
            with get_db_connection() as conn:
                c = conn.cursor()
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

                        if new_password:
                            c.execute("UPDATE passwords SET username=?, password=? WHERE username=?", (new_username, new_password, username))

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

# Register the class-based view with the app
app.add_url_rule('/add_user', view_func=AddUser.as_view('add_user'))
# Define a resource to return a list of users
class Users(Resource):
    def get(self):
        users = User.query.all()
        user_list = [{'id': user.id, 'name': user.name, 'email': user.email} for user in users]
        return jsonify(user_list)



# Add the resources to the API
api.add_resource(HelloWorld, '/')
api.add_resource(Users, '/users')
api.add_resource(Protected, '/protected')
api.add_resource(AddUser, '/add_user')
api.add_resource(Login, '/login')
api.add_resource(Register, '/register')
api.add_resource(DeleteAccount, '/delete_account')
api.add_resource(EditUser, '/edit_user')
api.add_resource(EditUserInfo, '/edit_user_info')


# Configure Swagger UI
SWAGGER_URL = '/swagger'
API_URL = '/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Sample API"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


@app.route('/swagger.json')
def swagger():
    with open('swagger.json', 'r') as f:
        return jsonify(json.load(f))

if __name__ == '__main__':
    app.run(debug=True)
