from flask import Flask
import os
from ecommerce import create_app

# Create Flask app
app = create_app()

# Configure app for Vercel
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'default-secret-key'),
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///ecommerce.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

# For Vercel serverless functions
def handler(request):
    """Entry point for Vercel serverless function"""
    return app
