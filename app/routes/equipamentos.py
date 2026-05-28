from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from app import db
from app.models import Equipamento

bp = Blueprint('equipamentos', __name__)

@bp.route('/equipamentos')
@login_required
def lista():
    return render_template('index.html')

@bp.route('/api/equipamentos', methods=['GET'])
@login_required
def api_listar():
    from app.models import Emprestimo
    from sqlalchemy import and_

    # IDs de equipamentos atualmente emprestados
    emprestados = db.session.query(Emprestimo.equipamento_id).filter(
        and_(
            Emprestimo.status.in_(['ativo', 'em_atraso']),
            Emprestimo.data_hora_devolucao_real == None
        )
    ).all()
    ids_emprestados = {e[0] for e in emprestados}

    equips = Equipamento.query.filter_by(ativo=True).order_by(Equipamento.nome).all()

    resultado = []
    for eq in equips:
        d = eq.to_dict()
        d['emprestado'] = eq.id in ids_emprestados
        resultado.append(d)

    return jsonify(resultado)

@bp.route('/api/equipamentos/todos', methods=['GET'])
@login_required
def api_todos():
    equips = Equipamento.query.order_by(Equipamento.nome).all()
    return jsonify([e.to_dict() for e in equips])

@bp.route('/api/equipamentos', methods=['POST'])
@login_required
def api_criar():
    data = request.get_json()
    try:
        eq = Equipamento(
            nome       = data['nome'],
            patrimonio = data['patrimonio'],
            descricao  = data.get('descricao', '')
        )
        db.session.add(eq)
        db.session.commit()
        return jsonify({'success': True, 'id': eq.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/equipamentos/<int:id>', methods=['PUT'])
@login_required
def api_editar(id):
    eq = Equipamento.query.get_or_404(id)
    data = request.get_json()
    eq.nome       = data.get('nome', eq.nome)
    eq.patrimonio = data.get('patrimonio', eq.patrimonio)
    eq.descricao  = data.get('descricao', eq.descricao)
    eq.ativo      = data.get('ativo', eq.ativo)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/equipamentos/<int:id>', methods=['DELETE'])
@login_required
def api_deletar(id):
    eq = Equipamento.query.get_or_404(id)
    eq.ativo = False
    db.session.commit()
    return jsonify({'success': True})