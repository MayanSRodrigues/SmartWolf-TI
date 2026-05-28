from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Usuario
from functools import wraps

bp = Blueprint('usuarios', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Acesso negado.'}), 403
        return f(*args, **kwargs)
    return decorated

@bp.route('/api/usuarios', methods=['GET'])
@login_required
@admin_required
def api_listar():
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    return jsonify([u.to_dict() for u in usuarios])

@bp.route('/api/usuarios', methods=['POST'])
@login_required
@admin_required
def api_criar():
    data = request.get_json()
    try:
        if Usuario.query.filter_by(email=data['email'].lower()).first():
            return jsonify({'success': False, 'error': 'E-mail já cadastrado.'}), 400
        u = Usuario(
            nome  = data['nome'],
            email = data['email'].strip().lower(),
            nivel = data.get('nivel', 'tecnico')
        )
        u.set_senha(data['senha'])
        db.session.add(u)
        db.session.commit()
        return jsonify({'success': True, 'id': u.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/usuarios/<int:id>', methods=['PUT'])
@login_required
@admin_required
def api_editar(id):
    u    = Usuario.query.get_or_404(id)
    data = request.get_json()
    try:
        u.nome  = data.get('nome', u.nome)
        u.email = data.get('email', u.email).strip().lower()
        u.nivel = data.get('nivel', u.nivel)
        u.ativo = data.get('ativo', u.ativo)
        if data.get('senha'):
            u.set_senha(data['senha'])
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/usuarios/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def api_deletar(id):
    if id == current_user.id:
        return jsonify({'success': False, 'error': 'Você não pode desativar sua própria conta.'}), 400
    u       = Usuario.query.get_or_404(id)
    u.ativo = False
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/usuarios/alterar_senha', methods=['POST'])
@login_required
def api_alterar_senha():
    data = request.get_json()
    if not current_user.verificar_senha(data.get('senha_atual', '')):
        return jsonify({'success': False, 'error': 'Senha atual incorreta.'}), 400
    current_user.set_senha(data['nova_senha'])
    db.session.commit()
    return jsonify({'success': True})