from flask import Flask
from ecommerce import create_app

app = create_app()

# This is required for Vercel serverless function
def handler(request):
    """Handle incoming requests."""
    with app.test_client() as client:
        # Forward the request to the Flask app
        resp = client.get(request.url)
        return resp.get_data(), resp.status_code, resp.headers.to_wsgi_list()
