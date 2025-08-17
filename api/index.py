from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to QuickShop!",
        "version": "1.0",
        "status": "online"
    })

@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy"
    })

def handler(request):
    """Serverless function handler for Vercel"""
    if request is None:
        return app
        
    try:
        path = request.get('path', '/')
        method = request.get('httpMethod', 'GET')

        with app.test_client() as client:
            response = client.open(path, method=method)
            
            return {
                'statusCode': response.status_code,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                },
                'body': response.get_data(as_text=True)
            }
            
    except Exception as e:
        print(f"Error: {str(e)}")  # This will show in Vercel logs
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': '{"error": "Internal Server Error"}'
        }
