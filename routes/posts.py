from flask import Blueprint, render_template, abort
from flask_login import current_user
from flask import request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Publication, Vote, Commentaire
from werkzeug.utils import secure_filename
import os
from flask import current_app
from models import Publication, Utilisateur, Notification, Message
from sqlalchemy import desc
from datetime import datetime
from sqlalchemy import or_




bp = Blueprint('posts', __name__)

@bp.route('/accueil')
def accueil():
    tri = request.args.get('tri')
    categorie = request.args.get('categorie')

    query = Publication.query

    if categorie:
        query = query.filter_by(catégorie=categorie)

    if tri == 'votes':
        publications = query.order_by(Publication.votes.desc()).all()
    else:
        publications = query.order_by(Publication.date_post.desc(), Publication.votes.desc()).all()

    # Calcul des statistiques pour l'utilisateur connecté (si authentifié)
    stats = None
    if current_user.is_authenticated:
        user = current_user
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

    return render_template('index.html', publications=publications, tri=tri, categorie=categorie, stats=stats)

@bp.route("/")
def root():
    return redirect(url_for('auth.intro'))

@bp.route('/poster', methods=['GET', 'POST'])
@login_required
def poster():
    if request.method == 'POST':
        titre = request.form['titre']
        texte = request.form['texte']
        url_post = request.form['url']
        catégorie = request.form['catégorie']

        # Gérer l’upload de fichier
        fichier = request.files['media']
        nom_fichier = None
        file_size = None
        if fichier and fichier.filename != '':
            nom_fichier = secure_filename(fichier.filename)
            chemin = os.path.join(current_app.config['UPLOAD_FOLDER'], nom_fichier)
            fichier.save(chemin)
            # Calculer la taille du fichier après sauvegarde
            file_size = os.path.getsize(chemin)

        nouvelle_pub = Publication(
            titre=titre,
            texte=texte,
            url=url_post if url_post else None,
            media=nom_fichier,
            file_size=file_size,  # Stocker la taille du fichier
            catégorie=catégorie,
            auteur_id=current_user.id,
            date_post=datetime.utcnow()
        )
        db.session.add(nouvelle_pub)
        db.session.commit()

        flash("Votre publication a été ajoutée.")
        return redirect(url_for('posts.accueil'))

    return render_template('post.html')

@bp.route('/vote/<int:publication_id>', methods=['POST'])
@login_required
def voter(publication_id):
    valeur = int(request.form['valeur'])  # +1 ou -1

    vote_existant = Vote.query.filter_by(user_id=current_user.id, publication_id=publication_id).first()
    publication = Publication.query.get_or_404(publication_id)

    if vote_existant:
        if vote_existant.valeur == valeur:
            # L'utilisateur clique à nouveau sur le même vote → annuler
            publication.votes -= valeur
            db.session.delete(vote_existant)
            db.session.commit()
            flash("Votre vote a été retiré.")
        else:
            # L'utilisateur change d'avis (de +1 à -1 ou inverse)
            publication.votes += 2 * valeur  # car il faut annuler l'ancien vote et ajouter le nouveau
            vote_existant.valeur = valeur
            db.session.commit()
            flash("Votre vote a été modifié.")
    else:
        # Premier vote
        nouveau_vote = Vote(user_id=current_user.id, publication_id=publication_id, valeur=valeur)
        publication.votes += valeur
        db.session.add(nouveau_vote)
        db.session.commit()
        flash("Merci pour votre vote !")

    return redirect(url_for('posts.accueil'))

def get_enfants(commentaire):
    return Commentaire.query.filter_by(parent_id=commentaire.id).order_by(Commentaire.date_comment.asc()).all()

@bp.route('/publication/<int:pub_id>')
def voir_publication(pub_id):
    publication = Publication.query.get_or_404(pub_id)
    commentaires = Commentaire.query.filter_by(publication_id=pub_id, parent_id=None).order_by(Commentaire.date_comment.asc()).all()
    return render_template('article.html', publication=publication, commentaires=commentaires, get_enfants=get_enfants)

@bp.route('/commenter/<int:pub_id>', methods=['POST'])
@login_required
def commenter(pub_id):
    contenu = request.form['contenu']
    parent_id = request.form.get('parent_id')

    commentaire = Commentaire(
        contenu=contenu,
        publication_id=pub_id,
        auteur_id=current_user.id,
        date_comment=datetime.utcnow(),
        parent_id=parent_id if parent_id else None
    )
    db.session.add(commentaire)
    db.session.commit()

    # notifier l’auteur du post
    if commentaire.auteur_id != current_user.id:
        notif = Notification(
            utilisateur_id=commentaire.auteur_id,
            type='commentaire',
            message=f"{current_user.nom} a commenté votre publication.",
            url=url_for('posts.voir_publication', pub_id= commentaire.publication_id),
            date=datetime.utcnow()
        )
        db.session.add(notif)
        db.session.commit()

    return redirect(url_for('posts.voir_publication', pub_id=pub_id))

@bp.route('/recherche')
def recherche():
    query = request.args.get('q')
    if not query:
        return redirect(url_for('posts.accueil'))

    # Recherche dans les publications
    publications = Publication.query.filter(
        or_(
            Publication.titre.ilike(f'%{query}%'),
            Publication.texte.ilike(f'%{query}%')
        )
    ).order_by(Publication.date_post.desc()).all()

    # Recherche dans les utilisateurs
    utilisateurs = Utilisateur.query.filter(
        or_(
            Utilisateur.nom.ilike(f'%{query}%'),
            Utilisateur.email.ilike(f'%{query}%')
        )
    ).order_by(Utilisateur.nom.asc()).all()

    return render_template('search_results.html', publications=publications, utilisateurs=utilisateurs, query=query)

@bp.route('/modifier/<int:pub_id>', methods=['GET', 'POST'])
@login_required
def modifier_publication(pub_id):
    publication = Publication.query.get_or_404(pub_id)

    if publication.auteur_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        # Stocker l'ancien nom du fichier média pour suppression ultérieure
        ancien_fichier = publication.media

        publication.titre = request.form['titre']
        publication.texte = request.form['texte']
        publication.catégorie = request.form['catégorie']
        publication.url = request.form['url']

        fichier = request.files.get('media')
        if fichier and fichier.filename != '':
            nom_fichier = secure_filename(fichier.filename)
            chemin = os.path.join(current_app.config['UPLOAD_FOLDER'], nom_fichier)
            fichier.save(chemin)
            # Calculer la taille du nouveau fichier
            file_size = os.path.getsize(chemin)
            publication.media = nom_fichier
            publication.file_size = file_size  # Mettre à jour la taille

            # Supprimer l'ancien fichier s'il existe
            if ancien_fichier:
                ancien_chemin = os.path.join(current_app.config['UPLOAD_FOLDER'], ancien_fichier)
                try:
                    if os.path.exists(ancien_chemin):
                        os.remove(ancien_chemin)
                except OSError as e:
                    flash(f"Erreur lors de la suppression de l'ancien fichier : {e}", "error")
        else:
            # Si aucun nouveau fichier n'est uploadé, conserver l'ancienne taille
            publication.file_size = publication.file_size if publication.media else None

        db.session.commit()
        flash("Publication modifiée.")
        return redirect(url_for('posts.voir_publication', pub_id=pub_id))

    return render_template('modifier_publication.html', publication=publication)

@bp.route('/supprimer/<int:pub_id>', methods=['POST'])
@login_required
def supprimer_publication(pub_id):
    publication = Publication.query.get_or_404(pub_id)
    if publication.auteur_id != current_user.id:
        abort(403)

    # Supprimer le fichier média s'il existe
    if publication.media:
        chemin_fichier = os.path.join(current_app.config['UPLOAD_FOLDER'], publication.media)
        try:
            if os.path.exists(chemin_fichier):
                os.remove(chemin_fichier)
        except OSError as e:
            flash(f"Erreur lors de la suppression du fichier : {e}", "error")

    db.session.delete(publication)
    db.session.commit()
    flash("Publication supprimée.")
    return redirect(url_for('posts.accueil'))

@bp.route('/commentaire/modifier/<int:comment_id>', methods=['GET', 'POST'])
@login_required
def modifier_commentaire(comment_id):
    commentaire = Commentaire.query.get_or_404(comment_id)
    if commentaire.auteur_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        commentaire.contenu = request.form['contenu']
        db.session.commit()
        flash("Commentaire modifié.")
        return redirect(url_for('posts.voir_publication', pub_id=commentaire.publication_id))

    return render_template('modifier_commentaire.html', commentaire=commentaire)

@bp.route('/commentaire/supprimer/<int:comment_id>', methods=['POST'])
@login_required
def supprimer_commentaire(comment_id):
    commentaire = Commentaire.query.get_or_404(comment_id)
    if commentaire.auteur_id != current_user.id:
        abort(403)

    pub_id = commentaire.publication_id
    db.session.delete(commentaire)
    db.session.commit()
    flash("Commentaire supprimé.")
    return redirect(url_for('posts.voir_publication', pub_id=pub_id))