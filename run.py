from ecommerce import create_app

from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello from QuickShop!'

# Import and initialize the main application
from ecommerce import create_app
app = create_app()

if __name__ == '__main__':
    app.run()

if __name__ == '__main__':
    app.run()