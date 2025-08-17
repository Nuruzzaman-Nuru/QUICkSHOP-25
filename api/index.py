from flask import Flask, send_from_directory
import os

app = Flask(__name__)

# Serve static files from the static directory
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Import the main application
from ecommerce import create_app
app = create_app()

if __name__ == '__main__':
    app.run()
