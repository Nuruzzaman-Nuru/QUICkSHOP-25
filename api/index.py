from flask import Flask
import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ecommerce import create_app

# Create Flask app
app = create_app()

# For Vercel serverless functions
def handler(request):
    """Handle requests in Vercel serverless function"""
    with app.test_client() as test_client:
        resp = test_client.get(request.get("path", "/"))
        return {
            "statusCode": resp.status_code,
            "headers": dict(resp.headers),
            "body": resp.get_data(as_text=True)
        }
