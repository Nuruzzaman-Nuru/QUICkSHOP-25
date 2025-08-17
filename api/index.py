from flask import Flask
from app import app

# For Vercel Serverless Function
def handler(request):
    return app
