from flask import Flask, render_template, jsonify, Blueprint
import requests



app = Flask(__name__)

# API URLs
API_PROTECTED_URL = 'http://localhost:5000/protected'
API_LOGIN_URL = 'http://localhost:5000/login'
API_REGISTER_URL = 'http://localhost:5000/register'
API_ADD_USER_URL = 'http://localhost:5000/add_user'
API_DELETE_ACCOUNT_URL = 'http://localhost:5000/delete_account'
API_EDIT_USER_URL = 'http://localhost:5000/edit_user'
API_EDIT_USER_INFO_URL = 'http://localhost:5000/edit_user_info'
API_USER_TOKENS_URL = 'http://localhost:5000/user_tokens'
API_ADD_WALLET_URL = 'http://localhost:5000/add_wallet'
API_DELETE_WALLET_URL = 'http://localhost:5000/delete_wallet'
API_EDIT_WALLET_URL = 'http://localhost:5000/edit_wallet'

@app.route('/')
def index():
    # Get data from APIs
    responses = {
        'protected': requests.get(API_PROTECTED_URL).json(),
        'login': requests.get(API_LOGIN_URL).json(),
        'register': requests.get(API_REGISTER_URL).json(),
        'add_user': requests.get(API_ADD_USER_URL).json(),
        'delete_account': requests.get(API_DELETE_ACCOUNT_URL).json(),
        'edit_user': requests.get(API_EDIT_USER_URL).json(),
        'edit_user_info': requests.get(API_EDIT_USER_INFO_URL).json(),
        'user_tokens': requests.get(API_USER_TOKENS_URL).json(),
        'add_wallet': requests.get(API_ADD_WALLET_URL).json(),
        'delete_wallet': requests.get(API_DELETE_WALLET_URL).json(),
        'edit_wallet': requests.get(API_EDIT_WALLET_URL).json(),
    }

    # Render HTML template with data
    #return render_template('index.html')
# Create a blueprint for the front UI
front_blueprint = Blueprint('front', __name__)

# Define a route for serving the index.html file
@front_blueprint.route('/index.html')
def front():
    return render_template('index.html')

# Define a route for serving the login.html file
@front_blueprint.route('/login.html')
def login():
    return render_template('login.html')


# Register the blueprint with the app
app.register_blueprint(front_blueprint, url_prefix='/')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
