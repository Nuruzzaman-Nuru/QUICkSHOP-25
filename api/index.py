from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to QuickShop API!",
        "status": "active"
    })

@app.route('/api/test')
def test():
    return jsonify({
        "message": "API test endpoint working!"
    })

def handler(request):
    """Handle requests in Vercel serverless function"""
    try:
        with app.test_client() as test_client:
            # Get the path from the request
            path = request.get('path', '/')
            
            # Make the request to Flask app
            response = test_client.get(path)
            
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
