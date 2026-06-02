from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Equipamento, Movimentacao, Categoria
from datetime import datetime

bp = Blueprint('inventario', __name__)

@bp.route('/api/categorias', methods=['GET'])
@login_required
def api_categorias():
    cats = Categoria.query.order_by(Categoria.nome).all()
    return jsonify([c.to_dict() for c in cats])

@bp.route('/api/categorias/seed', methods=['POST'])
def api_seed_categorias():
    if Categoria.query.count() > 0:
        return jsonify({'message': 'Categorias já existem'})
    categorias = [
        {'nome': 'Audiovisual', 'icone': '📽️'},
        {'nome': 'Informática', 'icone': '💻'},
        {'nome': 'Rede',        'icone': '🌐'},
        {'nome': 'Suprimentos', 'icone': '🔋'},
        {'nome': 'Telefonia',   'icone': '📞'},
        {'nome': 'Outros',      'icone': '📦'},
    ]
    for c in categorias:
        db.session.add(Categoria(nome=c['nome'], icone=c['icone']))
    db.session.commit()
    return jsonify({'success': True, 'message': '6 categorias criadas!'})

@bp.route('/api/categorias', methods=['POST'])
@login_required
def api_criar_categoria():
    data = request.get_json()
    try:
        cat = Categoria(
            nome  = data['nome'],
            icone = data.get('icone', '📦')
        )
        db.session.add(cat)
        db.session.commit()
        return jsonify({'success': True, 'id': cat.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/inventario', methods=['GET'])
@login_required
def api_inventario():
    tipo        = request.args.get('tipo')
    categoria   = request.args.get('categoria_id')
    alerta      = request.args.get('alerta')
    garantia    = request.args.get('garantia')

    query = Equipamento.query.filter_by(ativo=True)

    if tipo:
        query = query.filter_by(tipo=tipo)
    if categoria:
        query = query.filter_by(categoria_id=int(categoria))

    equipamentos = query.order_by(Equipamento.nome).all()

    resultado = []
    for e in equipamentos:
        d = e.to_dict()
        if alerta == 'true' and not e.estoque_baixo():
            continue
        if garantia == 'vencendo' and e.garantia_status() not in ('vencendo', 'vencida'):
            continue
        resultado.append(d)

    return jsonify(resultado)

@bp.route('/api/inventario/resumo', methods=['GET'])
@login_required
def api_resumo():
    todos = Equipamento.query.filter_by(ativo=True).all()

    total           = len(todos)
    emprestavel     = sum(1 for e in todos if e.tipo == 'emprestavel')
    fixo            = sum(1 for e in todos if e.tipo == 'fixo')
    suprimento      = sum(1 for e in todos if e.tipo == 'suprimento')
    estoque_baixo   = sum(1 for e in todos if e.estoque_baixo())
    garantia_alerta = sum(1 for e in todos if e.garantia_status() in ('vencendo', 'vencida'))

    return jsonify({
        'total':           total,
        'emprestavel':     emprestavel,
        'fixo':            fixo,
        'suprimento':      suprimento,
        'estoque_baixo':   estoque_baixo,
        'garantia_alerta': garantia_alerta
    })

@bp.route('/api/movimentacoes', methods=['GET'])
@login_required
def api_listar_movimentacoes():
    equipamento_id = request.args.get('equipamento_id')
    tipo           = request.args.get('tipo')

    query = Movimentacao.query.order_by(Movimentacao.criado_em.desc())

    if equipamento_id:
        query = query.filter_by(equipamento_id=int(equipamento_id))
    if tipo:
        query = query.filter_by(tipo=tipo)

    movs = query.limit(100).all()
    return jsonify([m.to_dict() for m in movs])

@bp.route('/api/movimentacoes', methods=['POST'])
@login_required
def api_criar_movimentacao():
    data = request.get_json()
    try:
        eq = Equipamento.query.get_or_404(int(data['equipamento_id']))

        mov = Movimentacao(
            equipamento_id = eq.id,
            tipo           = data['tipo'],
            quantidade     = int(data['quantidade']),
            motivo         = data.get('motivo', ''),
            responsavel    = data.get('responsavel', ''),
            observacoes    = data.get('observacoes', '')
        )

        # Atualiza quantidade no estoque
        if data['tipo'] == 'entrada':
            eq.quantidade += int(data['quantidade'])
        else:
            if eq.quantidade < int(data['quantidade']):
                return jsonify({'success': False, 'error': 'Quantidade insuficiente em estoque'}), 400
            eq.quantidade -= int(data['quantidade'])

        db.session.add(mov)
        db.session.commit()
        return jsonify({'success': True, 'id': mov.id, 'quantidade_atual': eq.quantidade}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/equipamentos', methods=['POST'])
@login_required
def api_criar_equipamento():
    data = request.get_json()
    try:
        eq = Equipamento(
            nome                = data['nome'],
            patrimonio          = data.get('patrimonio') or None,
            descricao           = data.get('descricao', ''),
            categoria_id        = data.get('categoria_id') or None,
            tipo                = data.get('tipo', 'emprestavel'),
            quantidade          = int(data.get('quantidade', 1)),
            quantidade_minima   = int(data.get('quantidade_minima', 1)),
            localizacao         = data.get('localizacao', ''),
            fornecedor          = data.get('fornecedor', ''),
            nota_fiscal         = data.get('nota_fiscal', ''),
            contrato_manutencao = data.get('contrato_manutencao', ''),
            data_compra         = datetime.strptime(data['data_compra'], '%Y-%m-%d').date() if data.get('data_compra') else None,
            garantia_ate        = datetime.strptime(data['garantia_ate'], '%Y-%m-%d').date() if data.get('garantia_ate') else None,
            valor_compra        = float(data['valor_compra']) if data.get('valor_compra') else None
        )
        db.session.add(eq)
        db.session.commit()
        return jsonify({'success': True, 'id': eq.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/inventario/<int:id>', methods=['PUT'])
@login_required
def api_editar_equipamento(id):
    eq   = Equipamento.query.get_or_404(id)
    data = request.get_json()
    try:
        eq.nome                = data.get('nome', eq.nome)
        eq.patrimonio          = data.get('patrimonio') or None
        eq.descricao           = data.get('descricao', eq.descricao)
        eq.categoria_id        = int(data['categoria_id']) if data.get('categoria_id') else None
        eq.tipo                = data.get('tipo', eq.tipo)
        eq.quantidade_minima   = int(data.get('quantidade_minima', eq.quantidade_minima))
        eq.localizacao         = data.get('localizacao', eq.localizacao)
        eq.fornecedor          = data.get('fornecedor', eq.fornecedor)
        eq.nota_fiscal         = data.get('nota_fiscal', eq.nota_fiscal)
        eq.contrato_manutencao = data.get('contrato_manutencao', eq.contrato_manutencao)
        eq.data_compra         = datetime.strptime(data['data_compra'], '%Y-%m-%d').date() if data.get('data_compra') else eq.data_compra
        eq.garantia_ate        = datetime.strptime(data['garantia_ate'], '%Y-%m-%d').date() if data.get('garantia_ate') else eq.garantia_ate
        eq.valor_compra        = float(data['valor_compra']) if data.get('valor_compra') else eq.valor_compra
        eq.ativo               = data.get('ativo', eq.ativo)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/equipamentos/<int:id>', methods=['DELETE'])
@login_required
def api_deletar_equipamento(id):
    eq       = Equipamento.query.get_or_404(id)
    eq.ativo = False
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/equipamentos/<int:id>/historico', methods=['GET'])
@login_required
def api_historico(id):
    movs  = Movimentacao.query.filter_by(equipamento_id=id).order_by(Movimentacao.criado_em.desc()).all()
    emps  = __import__('app.models', fromlist=['Emprestimo']).Emprestimo
    loans = emps.query.filter_by(equipamento_id=id).order_by(emps.criado_em.desc()).all()
    return jsonify({
        'movimentacoes': [m.to_dict() for m in movs],
        'emprestimos':   [e.to_dict() for e in loans]
    })

@bp.route('/api/inventario/<int:id>', methods=['GET'])
@login_required
def api_get_equipamento(id):
    eq = Equipamento.query.get_or_404(id)
    return jsonify(eq.to_dict())