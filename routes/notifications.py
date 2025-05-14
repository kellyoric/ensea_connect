from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Notification, db

bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@bp.route('/')
@login_required
def liste():
    notifs = Notification.query.filter_by(utilisateur_id=current_user.id).order_by(Notification.date.desc()).all()

    for n in notifs:
        n.lu = True
    db.session.commit()

    return render_template('notifications.html', notifications=notifs)
