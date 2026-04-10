import json
import os
from functools import wraps
from flask_login import LoginManager, UserMixin, current_user
from werkzeug.security import check_password_hash, generate_password_hash

login_manager = LoginManager()

class User(UserMixin):
    """Modelo de usuario simple"""
    
    def __init__(self, id, username, password_hash, role):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role
    
    def check_password(self, password):
        """Verifica la contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Verifica si el usuario es admin"""
        return self.role == "admin"

class UserManager:
    """Gestor de usuarios desde archivo JSON"""
    
    def __init__(self, users_file="data/users.json"):
        self.users_file = users_file
        self.users = {}
        self.load_users()
    
    def load_users(self):
        """Carga usuarios desde archivo JSON"""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                data = json.load(f)
                for user_data in data.get('users', []):
                    user = User(
                        id=user_data['id'],
                        username=user_data['username'],
                        password_hash=user_data['password_hash'],
                        role=user_data['role']
                    )
                    self.users[user.id] = user
        else:
            self.create_default_users()
    
    def create_default_users(self):
        """Crea usuarios por defecto si no existen"""
        default_users = [
            {
                'id': '1',
                'username': 'admin',
                'password_hash': generate_password_hash('admin123'),
                'role': 'admin'
            },
            {
                'id': '2',
                'username': 'viewer',
                'password_hash': generate_password_hash('viewer123'),
                'role': 'viewer'
            }
        ]
        
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        with open(self.users_file, 'w') as f:
            json.dump({'users': default_users}, f, indent=2)
        
        for user_data in default_users:
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                password_hash=user_data['password_hash'],
                role=user_data['role']
            )
            self.users[user.id] = user
    
    def get_user_by_id(self, user_id):
        """Obtiene usuario por ID"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username):
        """Obtiene usuario por username"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def authenticate(self, username, password):
        """Autentica un usuario"""
        user = self.get_user_by_username(username)
        if user and user.check_password(password):
            return user
        return None

user_manager = UserManager()

@login_manager.user_loader
def load_user(user_id):
    """Carga usuario para Flask-Login"""
    return user_manager.get_user_by_id(user_id)

def admin_required(f):
    """Decorador para rutas que requieren rol admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            return {"error": "Acceso denegado. Se requiere rol de administrador."}, 403
        return f(*args, **kwargs)
    return decorated_function
