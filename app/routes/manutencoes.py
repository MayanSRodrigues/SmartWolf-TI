from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Manutencao, Equipamento
from datetime import datetime

bp = Blueprint('manutencoes', __name__)

@bp.route('/api/manutencoes', methods=['GET'])
@login_required
def api_listar():
    status         = request.args.get('status')
    equipamento_id = request.args.get('equipamento_id')

    query = Manutencao.query.order_by(Manutencao.data_entrada.desc())

    if status:
        query = query.filter_by(status=status)
    if equipamento_id:
        query = query.filter_by(equipamento_id=int(equipamento_id))

    mans = query.all()
    return jsonify([m.to_dict() for m in mans])

@bp.route('/api/manutencoes', methods=['POST'])
@login_required
def api_criar():
    data = request.get_json()
    try:
        fmt = '%Y-%m-%dT%H:%M'
        man = Manutencao(
            equipamento_id = int(data['equipamento_id']),
            tipo           = data['tipo'],
            descricao      = data['descricao'],
            tecnico        = data.get('tecnico', ''),
            empresa        = data.get('empresa', ''),
            custo          = float(data['custo']) if data.get('custo') else None,
            data_entrada   = datetime.strptime(data['data_entrada'], fmt),
            data_saida     = datetime.strptime(data['data_saida'], fmt) if data.get('data_saida') else None,
            observacoes    = data.get('observacoes', '')
        )

        # Marca equipamento como em manutenção
        eq = Equipamento.query.get_or_404(int(data['equipamento_id']))
        if man.status == 'em_manutencao':
            eq.localizacao = 'Em manutenção'

        db.session.add(man)
        db.session.commit()
        return jsonify({'success': True, 'id': man.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/manutencoes/<int:id>', methods=['PUT'])
@login_required
def api_editar(id):
    man  = Manutencao.query.get_or_404(id)
    data = request.get_json()
    try:
        fmt = '%Y-%m-%dT%H:%M'
        man.tipo        = data.get('tipo', man.tipo)
        man.descricao   = data.get('descricao', man.descricao)
        man.tecnico     = data.get('tecnico', man.tecnico)
        man.empresa     = data.get('empresa', man.empresa)
        man.custo       = float(data['custo']) if data.get('custo') else man.custo
        man.data_saida  = datetime.strptime(data['data_saida'], fmt) if data.get('data_saida') else man.data_saida
        man.status      = data.get('status', man.status)
        man.observacoes = data.get('observacoes', man.observacoes)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/manutencoes/<int:id>/concluir', methods=['POST'])
@login_required
def api_concluir(id):
    man            = Manutencao.query.get_or_404(id)
    man.status     = 'concluida'
    man.data_saida = datetime.now()
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/manutencoes/<int:id>', methods=['DELETE'])
@login_required
def api_deletar(id):
    man = Manutencao.query.get_or_404(id)
    man.status = 'cancelada'
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/manutencoes/resumo', methods=['GET'])
@login_required
def api_resumo():
    em_manutencao = Manutencao.query.filter_by(status='em_manutencao').count()
    concluidas    = Manutencao.query.filter_by(status='concluida').count()
    canceladas    = Manutencao.query.filter_by(status='cancelada').count()

    from sqlalchemy import func
    custo_total = db.session.query(
        func.sum(Manutencao.custo)
    ).filter_by(status='concluida').scalar() or 0

    return jsonify({
        'em_manutencao': em_manutencao,
        'concluidas':    concluidas,
        'canceladas':    canceladas,
        'custo_total':   float(custo_total)
    })