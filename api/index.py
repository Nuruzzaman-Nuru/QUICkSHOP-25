from flask import Flask, Request
import os
from ecommerce import create_app

# Create Flask app
app = create_app()

# For Vercel serverless functions
def handler(request: Request):
    """Entry point for Vercel serverless function"""
    if request.method == "GET":
        with app.test_client() as test_client:
            response = test_client.get(request.path)
            return {
                "statusCode": response.status_code,
                "body": response.get_data(as_text=True),
                "headers": dict(response.headers)
            }
    return {
        "statusCode": 405,
        "body": "Method not allowed"
    }
