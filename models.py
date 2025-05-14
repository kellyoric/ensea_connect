from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Utilisateur(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.Text, default="")
    statut = db.Column(db.String(20), nullable=False, default="étudiant")
    photo = db.Column(db.String(255))

class Publication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200))
    texte = db.Column(db.Text)
    url = db.Column(db.String(300))
    media = db.Column(db.String(200))
    file_size = db.Column(db.BigInteger, nullable=True)  # Nouveau champ pour la taille du fichier en octets
    auteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_post = db.Column(db.DateTime, nullable=False)
    catégorie = db.Column(db.String(50))
    votes = db.Column(db.Integer, default=0)
    auteur = db.relationship('Utilisateur', backref='publications', lazy=True)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    publication_id = db.Column(db.Integer, db.ForeignKey('publication.id'), nullable=False)
    valeur = db.Column(db.Integer, nullable=False)

class Commentaire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contenu = db.Column(db.Text, nullable=False)
    publication_id = db.Column(db.Integer, db.ForeignKey('publication.id'), nullable=False)
    auteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    date_comment = db.Column(db.DateTime, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('commentaire.id'), nullable=True)
    auteur = db.relationship('Utilisateur', backref='commentaires')
    enfants = db.relationship('Commentaire', backref=db.backref('parent', remote_side=[id]), lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expediteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    destinataire_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date_envoi = db.Column(db.DateTime, nullable=False)
    expediteur = db.relationship('Utilisateur', foreign_keys=[expediteur_id], backref='messages_envoyes')
    destinataire = db.relationship('Utilisateur', foreign_keys=[destinataire_id], backref='messages_recus')
    lu = db.Column(db.Boolean, default=False)
    fichier = db.Column(db.String(200))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    type = db.Column(db.String(50))
    message = db.Column(db.Text)
    url = db.Column(db.String(200))
    date = db.Column(db.DateTime, nullable=False)
    lu = db.Column(db.Boolean, default=False)
    utilisateur = db.relationship('Utilisateur', backref='notifications')
