from ecommerce import create_app

app = create_app()

# These are required for WSGI servers to find the app
application = app
wsgi_app = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)