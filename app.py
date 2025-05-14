from flask import Flask
from config import Config
from models import db, Utilisateur, Message, Notification, Publication, Commentaire
from flask_login import LoginManager
from datetime import datetime
import os
from routes import messages, auth, posts, notifications, users
from flask_login import current_user
from flask_migrate import Migrate

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config.from_object(Config)
db.init_app(app)

migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    from models import Utilisateur
    return Utilisateur.query.get(int(user_id))

# Routes à venir

app.register_blueprint(auth.bp)
app.register_blueprint(posts.bp)
app.register_blueprint(messages.bp)
app.register_blueprint(notifications.bp)
app.register_blueprint(users.bp)

@app.context_processor
def inject_now():
    return {'current_year': datetime.now().year}

@app.context_processor
def inject_nb_messages():
    if current_user.is_authenticated:
        nb = Message.query.filter_by(destinataire_id=current_user.id, lu=False).count()
        return {'nb_nouveaux_messages': nb}
    return {'nb_nouveaux_messages': 0}

@app.context_processor
def inject_notifs():
    if current_user.is_authenticated:
        nb = Notification.query.filter_by(utilisateur_id=current_user.id, lu=False).count()
        return {'nb_notifications': nb}
    return {'nb_notifications': 0}

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host ='0.0.0.0', debug=True)
