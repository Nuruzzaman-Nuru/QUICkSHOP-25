import json

def handler(request):
    # Get the path from the request
    path = request.get('path', '/')
    
    # Handle different routes
    if path == '/':
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/html"
            },
            "body": "Welcome to QuickShop API!"
        }
    elif path == '/api/test':
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "status": "success",
                "message": "API is working!",
                "version": "1.0.0"
            })
        }
    else:
        return {
            "statusCode": 404,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": "Not Found",
                "message": "The requested path was not found"
            })
        }
