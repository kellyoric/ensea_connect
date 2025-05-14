from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

from models import db, Utilisateur, Publication, Commentaire, Message, Notification

bp = Blueprint('users', __name__, url_prefix='/utilisateur')

@bp.route('/modifier', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = current_user

    if request.method == 'POST':
        user.nom = request.form['nom']
        user.bio = request.form.get('bio')

        photo = request.files.get('photo')
        if photo and photo.filename != '':
            filename = secure_filename(photo.filename)
            path = os.path.join(current_app.root_path, 'static/uploads', filename)
            photo.save(path)
            user.photo = filename

        db.session.commit()
        flash("Profil mis à jour avec succès.")
        return redirect(url_for('posts.accueil'))

    return render_template('users/edit_profile.html', user=user)

@bp.route('/utilisateur/<int:user_id>/stats')
@login_required
def profile_stats(user_id):
    user = Utilisateur.query.get_or_404(user_id)

    # Calcul des vues du profil : compter les utilisateurs uniques qui ont interagi (hors l'utilisateur lui-même)
    # Inclut les auteurs de commentaires et destinataires de messages (hors l'utilisateur)
    vues_profil = (db.session.query(Commentaire.auteur_id)
                   .filter(Commentaire.auteur_id != user.id, Commentaire.publication_id.in_(
                       db.session.query(Publication.id).filter(Publication.auteur_id == user.id)))
                   .distinct().count() +
                   db.session.query(Message.expediteur_id)
                   .filter(Message.destinataire_id == user.id, Message.expediteur_id != user.id)
                   .distinct().count())

    stats = {
        "vues_profil": vues_profil,
        "messages_envoyes": Message.query.filter_by(expediteur_id=user.id).count(),
        "messages_recus": Message.query.filter_by(destinataire_id=user.id).count(),
        "commentaires": Commentaire.query.filter_by(auteur_id=user.id).count(),
        "publications": Publication.query.filter_by(auteur_id=user.id).count(),
        "notifications": Notification.query.filter_by(utilisateur_id=user.id).count(),
    }
    return render_template("users/stats.html", user=user, stats=stats)