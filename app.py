from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from ecommerce.models.shop import Shop

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, 
        template_folder='ecommerce/templates',
        static_folder='ecommerce/static',
        static_url_path='')

    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'  # Simplified path for Vercel
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints
    from ecommerce.routes.auth import auth_bp
    from ecommerce.routes.shop import shop_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)

    @app.route('/')
    def home():
        featured_shops = Shop.query.filter_by(is_active=True).limit(6).all()
        return render_template('main/home.html', featured_shops=featured_shops)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
