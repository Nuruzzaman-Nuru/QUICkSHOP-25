from flask import Flask, jsonify, request

app = Flask(__name__)

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
    try:
        with app.test_client() as test_client:
            # Get the path from the request, defaulting to '/'
            path = request.get('path', '/')
            
            # Get the method from the request, defaulting to 'GET'
            method = request.get('httpMethod', 'GET')
            
            # Make the request to the Flask app
            response = test_client.open(path, method=method)
            
            return {
                "statusCode": response.status_code,
                "headers": dict(response.headers),
                "body": response.get_data(as_text=True)
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": str(e)
        }
