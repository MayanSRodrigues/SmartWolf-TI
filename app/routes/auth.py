from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Usuario
from datetime import datetime

bp = Blueprint('auth', __name__)

@bp.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('emprestimos.index'))
    return render_template('login.html')

@bp.route('/api/auth/login', methods=['POST'])
def api_login():
    data  = request.get_json()
    email = data.get('email', '').strip().lower()
    senha = data.get('senha', '')

    usuario = Usuario.query.filter_by(email=email, ativo=True).first()

    if not usuario or not usuario.verificar_senha(senha):
        return jsonify({'success': False, 'error': 'E-mail ou senha incorretos.'}), 401

    login_user(usuario, remember=True)
    usuario.ultimo_acesso = datetime.now()
    db.session.commit()

    return jsonify({
        'success': True,
        'usuario': {
            'nome':  usuario.nome,
            'email': usuario.email,
            'nivel': usuario.nivel
        }
    })

@bp.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify({'success': True})

@bp.route('/api/auth/me', methods=['GET'])
@login_required
def api_me():
    return jsonify(current_user.to_dict())

@bp.route('/api/setup', methods=['POST'])
def api_setup():
    if Usuario.query.count() > 0:
        return jsonify({'error': 'Setup já realizado'}), 400
    data = request.get_json()
    u = Usuario(
        nome  = data.get('nome', 'Admin'),
        email = data.get('email'),
        nivel = 'admin'
    )
    u.set_senha(data.get('senha'))
    db.session.add(u)
    db.session.commit()
    return jsonify({'success': True, 'message': f'Usuário {u.email} criado!'})