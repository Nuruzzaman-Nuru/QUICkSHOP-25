from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to QuickShop API!"

@app.route('/api/test')
def test():
    return jsonify({
        "status": "success",
        "message": "API is working!"
    })

# For local testing
if __name__ == '__main__':
    app.run()
