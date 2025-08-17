from flask import Flask, Response
import os

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'default-secret-key'),
)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return "Hello from QuickShop!", 200

def handler(request):
    with app.test_client() as test_client:
        response = test_client.get(request.get("path", "/"))
        return Response(
            response.get_data(),
            status=response.status_code,
            headers=dict(response.headers)
        )
