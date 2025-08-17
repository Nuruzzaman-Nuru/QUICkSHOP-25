from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "Welcome to QuickShop!",
        "status": "online"
    })

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        "message": "API is working"
    })

# Vercel serverless handler
def handler(request):
    if request is None:
        # Handle direct Flask calls
        return app
        
    try:
        http_method = request.get('httpMethod', 'GET')
        path = request.get('path', '/')
        
        with app.test_client() as client:
            response = client.open(path, method=http_method)
            
            return {
                'statusCode': response.status_code,
                'headers': {'Content-Type': 'application/json'},
                'body': response.get_data(as_text=True)
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }
