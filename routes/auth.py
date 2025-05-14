from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from flask import current_app
import os

from models import db, Utilisateur, Message, Publication, Commentaire, Notification
from sqlalchemy import or_

bp = Blueprint('auth', __name__)

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        nom = request.form['nom']
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']
        bio = request.form.get('bio')
        fichier_photo = request.files['photo']
        statut = request.form.get('statut', 'étudiant')
        nom_fichier = None

        if fichier_photo and fichier_photo.filename != '':
            nom_fichier = secure_filename(fichier_photo.filename)
            chemin = os.path.join(current_app.root_path, 'static/uploads', nom_fichier)
            fichier_photo.save(chemin)

        user_exist = Utilisateur.query.filter_by(email=email).first()
        if user_exist:
            flash("Un compte avec cet email existe déjà.")
            return redirect(url_for('auth.signup'))

        hashed_pw = generate_password_hash(mot_de_passe, method='pbkdf2:sha256')
        new_user = Utilisateur(nom=nom, email=email, mot_de_passe=hashed_pw, photo=nom_fichier, bio=bio, statut=statut)

        db.session.add(new_user)
        db.session.commit()

        flash("Compte créé avec succès. Connectez-vous.")
        return redirect(url_for('auth.login'))

    return render_template('signup.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']

        user = Utilisateur.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.mot_de_passe, mot_de_passe):
            flash("Email ou mot de passe incorrect.")
            return redirect(url_for('auth.login'))

        login_user(user)
        return redirect(url_for('posts.accueil'))

    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route("/intro")
def intro():
    return render_template("intro.html")

@bp.route('/profil/<int:id>')
def profil(id):
    utilisateur = Utilisateur.query.get_or_404(id)
    publications = Publication.query.filter_by(auteur_id=utilisateur.id).order_by(Publication.date_post.desc()).all()
    return render_template('profil.html', utilisateur=utilisateur, publications=publications)


# ===== NOUVELLE ROUTE : Statistiques de profil =====

