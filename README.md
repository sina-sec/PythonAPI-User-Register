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
