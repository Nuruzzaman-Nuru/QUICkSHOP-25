from ecommerce import create_app

app = create_app()

# This is required for Vercel to find the app
application = app

if __name__ == '__main__':
    app.run()