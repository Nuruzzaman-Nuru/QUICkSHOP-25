from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/')
def home():
    return "Welcome to QuickShop!", 200

if __name__ == '__main__':
    app.run()
