from ecommerce import create_app

app = create_app()

# This is required for Vercel serverless function
def handler(request, context):
    return app(request)
