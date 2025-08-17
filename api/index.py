def handler(request):
    """
    Simple handler function for Vercel
    """
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': '{"message": "Hello from QuickShop!"}'
    }
