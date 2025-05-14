from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Message, Utilisateur, Notification
from werkzeug.utils import secure_filename
import os
import logging

# Configurer le logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

bp = Blueprint('messages', __name__, url_prefix='/messages')

@bp.route('/')
@login_required
def boite_reception():
    logger.debug(f"Current user: {current_user}, ID: {getattr(current_user, 'id', 'Non défini')}")
    expediteurs = db.session.query(Message.expediteur_id).filter_by(destinataire_id=current_user.id)
    destinataires = db.session.query(Message.destinataire_id).filter_by(expediteur_id=current_user.id)

    interlocuteurs_ids = set([r[0] for r in expediteurs.union(destinataires).all() if r[0] != current_user.id])

    conversations = []

    for user_id in interlocuteurs_ids:
        user = Utilisateur.query.get(user_id)
        messages = Message.query.filter(
            ((Message.expediteur_id == current_user.id) & (Message.destinataire_id == user_id)) |
            ((Message.expediteur_id == user_id) & (Message.destinataire_id == current_user.id))
        ).order_by(Message.date_envoi.desc()).limit(5).all()
        messages.reverse()
        has_unread = any(msg.destinataire_id == current_user.id and not msg.lu for msg in messages)
        conversations.append({
            'interlocuteur': user,
            'messages': messages,
            'has_unread': has_unread
        })

    return render_template('messages/inbox.html', conversations=conversations)

@bp.route('/api/inbox', methods=['GET'])
@login_required
def api_inbox():
    expediteurs = db.session.query(Message.expediteur_id).filter_by(destinataire_id=current_user.id)
    destinataires = db.session.query(Message.destinataire_id).filter_by(expediteur_id=current_user.id)

    interlocuteurs_ids = set([r[0] for r in expediteurs.union(destinataires).all() if r[0] != current_user.id])

    conversations = []

    for user_id in interlocuteurs_ids:
        user = Utilisateur.query.get(user_id)
        messages = Message.query.filter(
            ((Message.expediteur_id == current_user.id) & (Message.destinataire_id == user_id)) |
            ((Message.expediteur_id == user_id) & (Message.destinataire_id == current_user.id))
        ).order_by(Message.date_envoi.desc()).limit(5).all()
        messages.reverse()
        has_unread = any(msg.destinataire_id == current_user.id and not msg.lu for msg in messages)
        conversations.append({
            'interlocuteur': {
                'id': user.id,
                'nom': user.nom,
                'photo': user.photo if user.photo else None
            },
            'messages': [
                {
                    'expediteur_id': msg.expediteur_id,
                    'expediteur_nom': msg.expediteur.nom,
                    'contenu': msg.contenu,
                    'date_envoi': msg.date_envoi.strftime('%d/%m/%Y %H:%M')
                } for msg in messages
            ],
            'has_unread': has_unread
        })

    return jsonify({'conversations': conversations})

@bp.route('/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_message():
    if request.method == 'POST':
        destinataire_id = request.form['destinataire_id']
        contenu = request.form.get('contenu', '')
        fichier = request.files.get('fichier')
        nom_fichier = None

        if fichier and fichier.filename != '':
            nom_fichier = secure_filename(fichier.filename)
            chemin = os.path.join(current_app.root_path, 'static/uploads', nom_fichier)
            logger.debug(f"Sauvegarde du fichier à : {chemin}")
            fichier.save(chemin)
        else:
            logger.debug("Aucun fichier reçu dans la requête POST.")

        msg = Message(
            expediteur_id=current_user.id,
            destinataire_id=destinataire_id,
            contenu=contenu,
            fichier=nom_fichier,
            date_envoi=datetime.utcnow(),
            lu=False
        )

        logger.debug(f"Message créé : contenu={contenu}, fichier={nom_fichier}")

        db.session.add(msg)
        db.session.commit()

        notif = Notification(
            utilisateur_id=destinataire_id,
            type='message',
            message=f"{current_user.nom} vous a envoyé un nouveau message.",
            url=url_for('messages.boite_reception'),
            date=datetime.utcnow()
        )
        db.session.add(notif)
        db.session.commit()

        return redirect(url_for('messages.boite_reception'))

    utilisateurs = Utilisateur.query.filter(Utilisateur.id != current_user.id).all()
    return render_template('messages/nouveau.html', utilisateurs=utilisateurs)

@bp.route('/conversation/<int:utilisateur_id>', methods=['GET', 'POST'])
@login_required
def conversation(utilisateur_id):
    interlocuteur = Utilisateur.query.get_or_404(utilisateur_id)

    if request.method == 'POST':
        contenu = request.form.get('contenu', '').strip()
        fichier = request.files.get('fichier')
        nom_fichier = None

        # Vérifier si un fichier est envoyé
        if fichier and fichier.filename != '':
            nom_fichier = secure_filename(fichier.filename)
            chemin = os.path.join(current_app.root_path, 'static/uploads', nom_fichier)
            logger.debug(f"Sauvegarde du fichier à : {chemin}")
            try:
                fichier.save(chemin)
                logger.debug(f"Fichier sauvegardé avec succès : {nom_fichier}")
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde du fichier : {str(e)}")
                return jsonify({'success': False, 'error': 'Erreur lors de la sauvegarde du fichier'}), 500
        else:
            logger.debug("Aucun fichier reçu dans la requête POST.")

        # Vérifier si contenu ou fichier est présent
        if not contenu and not nom_fichier:
            logger.error("Ni contenu ni fichier fourni dans la requête POST.")
            return jsonify({'success': False, 'error': 'Le message doit contenir du texte ou un fichier'}), 400

        msg = Message(
            expediteur_id=current_user.id,
            destinataire_id=interlocuteur.id,
            contenu=contenu,
            fichier=nom_fichier,
            date_envoi=datetime.utcnow(),
            lu=False
        )
        logger.debug(f"Message créé : contenu={contenu}, fichier={nom_fichier}")

        db.session.add(msg)
        db.session.commit()

        return jsonify({'success': True})

    messages = Message.query.filter(
        ((Message.expediteur_id == current_user.id) & (Message.destinataire_id == interlocuteur.id)) |
        ((Message.expediteur_id == interlocuteur.id) & (Message.destinataire_id == current_user.id))
    ).order_by(Message.date_envoi.asc()).all()

    for m in messages:
        if m.destinataire_id == current_user.id and not m.lu:
            m.lu = True
    db.session.commit()

    return render_template('messages/conversation.html', messages=messages, interlocuteur=interlocuteur)

@bp.route('/api/conversation/<int:utilisateur_id>', methods=['GET'])
@login_required
def api_conversation(utilisateur_id):
    interlocuteur = Utilisateur.query.get_or_404(utilisateur_id)

    messages = Message.query.filter(
        ((Message.expediteur_id == current_user.id) & (Message.destinataire_id == interlocuteur.id)) |
        ((Message.expediteur_id == interlocuteur.id) & (Message.destinataire_id == current_user.id))
    ).order_by(Message.date_envoi.asc()).all()

    for m in messages:
        if m.destinataire_id == current_user.id and not m.lu:
            m.lu = True
    db.session.commit()

    messages_data = [
        {
            'expediteur_id': msg.expediteur_id,
            'expediteur_nom': msg.expediteur.nom,
            'expediteur_photo': msg.expediteur.photo if msg.expediteur.photo else None,
            'contenu': msg.contenu,
            'fichier': msg.fichier,
            'date_envoi': msg.date_envoi.strftime('%d/%m/%Y %H:%M')
        }
        for msg in messages
    ]

    return jsonify({
        'interlocuteur': {
            'id': interlocuteur.id,
            'nom': interlocuteur.nom,
            'photo': interlocuteur.photo if interlocuteur.photo else None
        },
        'messages': messages_data,
        'current_user_id': current_user.id
    })