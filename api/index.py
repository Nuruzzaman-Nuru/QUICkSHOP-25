from flask import Flask, jsonify

app = Flask(__name__)

def create_app():
    return app

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Hello from QuickShop!"})

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"status": "API is working!"})

# This is important for Vercel
def handler(request):
    """Handle requests in Vercel serverless function"""
    if request.method == "GET":
        if request.path == "/":
            return home()
        elif request.path == "/api/test":
            return test()
    return jsonify({"error": "Not Found"}), 404
