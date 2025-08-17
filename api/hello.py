from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ecommerce.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)

@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to QuickShop API!",
        "status": "active",
        "version": "1.0.0"
    })

@app.route('/api/products')
def products():
    # Mock product data
    products = [
        {"id": 1, "name": "Product 1", "price": 99.99},
        {"id": 2, "name": "Product 2", "price": 149.99},
        {"id": 3, "name": "Product 3", "price": 199.99}
    ]
    return jsonify({"products": products})

@app.route('/api/categories')
def categories():
    # Mock category data
    categories = [
        {"id": 1, "name": "Electronics"},
        {"id": 2, "name": "Clothing"},
        {"id": 3, "name": "Books"}
    ]
    return jsonify({"categories": categories})

def handler(request):
    """Handle requests in Vercel serverless function"""
    with app.test_client() as test_client:
        response = test_client.get(request.get('path', '/'))
        return {
            "statusCode": response.status_code,
            "headers": dict(response.headers),
            "body": response.get_data(as_text=True)
        }
