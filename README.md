# PythonAPI-User-Register
An API for creating a user - creating a token for a specified time - creating a user account - with the ability to edit and delete in different parts




The provided code sets up a Flask application with user authentication, registration, and wallet management features, storing data in an SQLite database. Below is a summary and explanation of each part:

### 1- Importing Libraries:

---
```
 import jwt
 import datetime
 import secrets
 from functools import wraps
 from flask import Flask, request, jsonify
 import sqlite3
 import requests
```

### 2- Application Setup:
```
app = Flask(__name__)
SECRET_KEY = secrets.token_hex(16)
```

### 3- Database Connection and Table Creation:
```
get_db_connection(): Establishes a connection to the SQLite database.
create_users_table(), create_tokens_table(), create_passwords_table(), create_wallets_table(): Functions to create necessary tables if they do not exist.
create_database_tables(): Calls the above functions to ensure all tables are created.
```
### 4- Routes:
```
/protected: Protected route example that returns a message for authenticated users.
/login: Authenticates users and generates tokens.
/register: Registers new users.
/add_user: Adds a new user.
/delete_account: Deletes a user account.
/edit_user: Edits user's username and password.
/edit_user_info: Edits user's personal information.
/user_tokens: Returns all user tokens.
/add_wallet: Adds a new wallet for the user.
/delete_wallet: Deletes a user's wallet.
/edit_wallet: Edits an existing wallet.
```
### 5- Helper Functions:
```
authenticate_user(username, password): Verifies the user's password.
get_user_tokens(): Retrieves all user tokens from the database.
```

##### Detailed Code Explanation:
### 1- Generating a Secret Key:
```
SECRET_KEY = secrets.token_hex(16)
```
Generates a random 32-character hexadecimal string used as the secret key for encoding JWT tokens.

### 2- Database Connection:

```
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

```
Establishes a connection to the users.db SQLite database and configures the connection to return rows as dictionaries.

### 3- Table Creation Functions:

Table Creation Functions:
```
def create_users_table():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (username TEXT PRIMARY KEY, first_name TEXT, last_name TEXT, age INTEGER, phone_number TEXT)''')

```
Similar functions are created for tokens, passwords, and wallets tables.

### 4- JWT Token Functions:

```
def generate_token(username):
    payload = {
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

```
Generates a JWT token with an expiration time of 30 minutes.

```
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

```
Decorator function to ensure the request has a valid JWT token.

### 5- Route Implementations:
```
- Protected Route:
@app.route('/protected')
@token_required
def protected(username):
    return jsonify({'message': f'Hello, {username}! This is a protected endpoint.'})
```
- user Registration:
```
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
                c.execute("INSERT INTO passwords (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                return jsonify({'message': 'Registration successful!'})
            except sqlite3.IntegrityError:
                return jsonify({'message': 'Username already exists!'}), 400
    else:
        return jsonify({'message': 'Missing username or password!'}), 400

```
### 6- Wallet Management:

- Add Wallet:
```
@app.route('/add_wallet', methods=['POST'])
@token_required
def add_wallet(username):
    data = request.json
    balance = data.get('balance')
    wallet_type = data.get('wallet_type')
    currency = data.get('currency')
    description = data.get('description')
    status = data.get('status')
    created_at = datetime.datetime.now()
    last_updated_at = created_at

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

```


#### Running the Application:
```
if __name__ == '__main__':
    app.run(debug=True)

```

Starts the Flask application in debug mode, making it easier to develop and troubleshoot.

This setup provides a basic but functional example of user authentication, user registration, and wallet management using Flask and SQLite, with JWT for secure authentication.




#####  To communicate with this API through curl, you need to send the appropriate HTTP requests to different routes. Below are the curl commands for each root.

### - 1. Register a new user ('/register')
```
curl -X POST http://localhost:5000/register -H "Content-Type: application/json" -d '{
    "username": "your_username",
    "password": "your_password",
    "first_name": "YourFirstName",
    "last_name": "YourLastName",
    "age": 25,
    "phone_number": "1234567890"
}'

```
### - 2- 2. Login and get a token ('/login')
```
curl -X POST http://localhost:5000/login -H "Content-Type: application/json" -d '{
    "username": "your_username",
    "password": "your_password"
}'

```
### - 3. Access a protected route ('/protected')

```
curl -X GET http://localhost:5000/protected -H "Authorization: Bearer your_jwt_token"

```
### - 4. Add a new user ('/add_user')

```
curl -X POST http://localhost:5000/add_user -H "Content-Type: application/json" -d '{
    "username": "new_username",
    "password": "new_password",
    "first_name": "NewFirstName",
    "last_name": "NewLastName",
    "age": 30,
    "phone_number": "0987654321"
}'

```
### - 5. Delete an account ('/delete_account')

```
curl -X POST http://localhost:5000/delete_account -H "Authorization: Bearer your_jwt_token" -H "Content-Type: application/json" -d '{
    "password": "your_password"
}'

```
### - 6. Edit user information ('/edit_user')

```
curl -X POST http://localhost:5000/edit_user -H "Authorization: Bearer your_jwt_token" -H "Content-Type: application/json" -d '{
    "new_username": "new_username",
    "new_password": "new_password",
    "current_password": "your_current_password"
}'

```
### - 7. Edit user details ('/edit_user_info')

```
curl -X POST http://localhost:5000/edit_user_info -H "Authorization: Bearer your_jwt_token" -H "Content-Type: application/json" -d '{
    "new_first_name": "NewFirstName",
    "new_last_name": "NewLastName",
    "new_age": 28,
    "new_phone_number": "1122334455",
    "new_password": "new_password",
    "current_password": "your_current_password",
    "new_username": "new_username"
}'

```
### - 8. List all user tokens ('/user_tokens')

```
curl -X GET http://localhost:5000/user_tokens

```
### - 9. Add a wallet to a user account ('/add_wallet')

```
curl -X POST http://localhost:5000/add_wallet -H "Authorization: Bearer your_jwt_token" -H "Content-Type: application/json" -d '{
    "balance": 1000,
    "wallet_type": "personal",
    "currency": "USD",
    "description": "My wallet",
    "status": "active"
}'

```
### - 10. Delete a wallet ('/delete_wallet')

```
curl -X POST http://localhost:5000/delete_wallet -H "Authorization: Bearer your_jwt_token" -H "Content-Type: application/json" -d '{
    "password": "your_password",
    "username": "your_username"
}'

```
### - 11. Edit a wallet ('/edit_wallet')

```
curl -X POST http://localhost:5000/edit_wallet -H "Authorization: Bearer your_jwt_token" -H "Content-Type: application/json" -d '{
    "balance": 2000,
    "wallet_type": "business",
    "currency": "EUR",
    "description": "Updated wallet",
    "status": "inactive"
}'

```
######  For each protected request, replace your_jwt_token with the JWT token obtained from the /login endpoint. Also, replace the placeholder values (e.g., your_username, your_password, etc.) with actual data.
