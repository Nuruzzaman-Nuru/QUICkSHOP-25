from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello from QuickShop!'

@app.route('/api/test')
def test():
    return {"message": "API is working!"}
