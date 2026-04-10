from flask import Flask
from flask_socketio import SocketIO
from config_flask import FlaskConfig
from dashboard.auth import login_manager
from dashboard.routes import bp
from scheduler_api import scheduler_bp

app = Flask(__name__)
app.config.from_object(FlaskConfig)

login_manager.init_app(app)
login_manager.login_view = 'main.login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

socketio = SocketIO(app, async_mode=FlaskConfig.SOCKETIO_ASYNC_MODE, cors_allowed_origins=FlaskConfig.SOCKETIO_CORS_ALLOWED_ORIGINS)

# Register blueprints
app.register_blueprint(bp)
app.register_blueprint(scheduler_bp)

if __name__ == '__main__':
    socketio.run(
        app,
        host=FlaskConfig.HOST,
        port=FlaskConfig.PORT,
        debug=FlaskConfig.DEBUG
    )
