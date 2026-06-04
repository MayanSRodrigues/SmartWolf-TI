from flask import Blueprint, request, jsonify
from flask_login import login_required
from app import db
from app.models import Equipamento, Movimentacao, Categoria
from datetime import datetime

bp = Blueprint('inventario', __name__)

# ── CATEGORIAS ──────────────────────────────────────────────────

@bp.route('/api/categorias', methods=['GET'])
@login_required
def api_categorias():
    cats = Categoria.query.order_by(Categoria.nome).all()
    return jsonify([c.to_dict() for c in cats])

@bp.route('/api/categorias', methods=['POST'])
@login_required
def api_criar_categoria():
    data = request.get_json()
    try:
        cat = Categoria(nome=data['nome'], icone=data.get('icone', '📦'))
        db.session.add(cat)
        db.session.commit()
        return jsonify({'success': True, 'id': cat.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

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

# ── INVENTÁRIO ──────────────────────────────────────────────────

def _parse_equipamento(data, eq=None):
    """Monta ou atualiza um objeto Equipamento a partir do payload."""
    novo = eq is None
    obj  = eq or Equipamento()

    obj.nome                = data.get('nome', obj.nome if not novo else '')
    obj.patrimonio          = data.get('patrimonio') or None
    obj.descricao           = data.get('descricao', obj.descricao if not novo else '')
    obj.categoria_id        = int(data['categoria_id']) if data.get('categoria_id') else None
    obj.tipo                = data.get('tipo', obj.tipo if not novo else 'emprestavel')
    obj.localizacao         = data.get('localizacao', obj.localizacao if not novo else '')
    obj.fornecedor          = data.get('fornecedor', obj.fornecedor if not novo else '')
    obj.nota_fiscal         = data.get('nota_fiscal', obj.nota_fiscal if not novo else '')
    obj.contrato_manutencao = data.get('contrato_manutencao', obj.contrato_manutencao if not novo else '')
    obj.valor_compra        = float(data['valor_compra']) if data.get('valor_compra') else (obj.valor_compra if not novo else None)

    if data.get('data_compra'):
        obj.data_compra = datetime.strptime(data['data_compra'], '%Y-%m-%d').date()
    elif not novo:
        pass  # mantém o valor existente

    if data.get('garantia_ate'):
        obj.garantia_ate = datetime.strptime(data['garantia_ate'], '%Y-%m-%d').date()
    elif not novo:
        pass

    if novo:
        obj.quantidade        = int(data.get('quantidade', 1))
        obj.quantidade_minima = int(data.get('quantidade_minima', 1))
    else:
        obj.quantidade_minima = int(data.get('quantidade_minima', obj.quantidade_minima))
        obj.ativo             = data.get('ativo', obj.ativo)

    return obj

@bp.route('/api/inventario', methods=['GET'])
@login_required
def api_inventario():
    tipo      = request.args.get('tipo')
    categoria = request.args.get('categoria_id')
    alerta    = request.args.get('alerta')
    garantia  = request.args.get('garantia')

    query = Equipamento.query.filter_by(ativo=True)
    if tipo:      query = query.filter_by(tipo=tipo)
    if categoria: query = query.filter_by(categoria_id=int(categoria))

    resultado = []
    for e in query.order_by(Equipamento.nome).all():
        if alerta == 'true' and not e.estoque_baixo():
            continue
        if garantia == 'vencendo' and e.garantia_status() not in ('vencendo', 'vencida'):
            continue
        resultado.append(e.to_dict())

    return jsonify(resultado)

@bp.route('/api/inventario', methods=['POST'])
@login_required
def api_criar_inventario():
    """Cria novo item com TODOS os campos do inventário."""
    data = request.get_json()
    try:
        eq = _parse_equipamento(data)
        db.session.add(eq)
        db.session.commit()
        return jsonify({'success': True, 'id': eq.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/inventario/resumo', methods=['GET'])
@login_required
def api_resumo():
    todos = Equipamento.query.filter_by(ativo=True).all()
    return jsonify({
        'total':           len(todos),
        'emprestavel':     sum(1 for e in todos if e.tipo == 'emprestavel'),
        'fixo':            sum(1 for e in todos if e.tipo == 'fixo'),
        'suprimento':      sum(1 for e in todos if e.tipo == 'suprimento'),
        'estoque_baixo':   sum(1 for e in todos if e.estoque_baixo()),
        'garantia_alerta': sum(1 for e in todos if e.garantia_status() in ('vencendo', 'vencida'))
    })

@bp.route('/api/inventario/<int:id>', methods=['GET'])
@login_required
def api_get_equipamento(id):
    eq = Equipamento.query.get_or_404(id)
    return jsonify(eq.to_dict())

@bp.route('/api/inventario/<int:id>', methods=['PUT'])
@login_required
def api_editar_equipamento(id):
    eq   = Equipamento.query.get_or_404(id)
    data = request.get_json()
    try:
        _parse_equipamento(data, eq)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

# ── EQUIPAMENTOS (rota legada usada pelo módulo de empréstimos) ──

@bp.route('/api/equipamentos', methods=['POST'])
@login_required
def api_criar_equipamento():
    """Rota legada — cria equipamento simples (usado em empréstimos)."""
    data = request.get_json()
    try:
        eq = Equipamento(
            nome       = data['nome'],
            patrimonio = data.get('patrimonio') or None,
            descricao  = data.get('descricao', ''),
            tipo       = data.get('tipo', 'emprestavel'),
            quantidade = int(data.get('quantidade', 1)),
        )
        db.session.add(eq)
        db.session.commit()
        return jsonify({'success': True, 'id': eq.id}), 201
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
    from app.models import Emprestimo
    movs  = Movimentacao.query.filter_by(equipamento_id=id).order_by(Movimentacao.criado_em.desc()).all()
    loans = Emprestimo.query.filter_by(equipamento_id=id).order_by(Emprestimo.criado_em.desc()).all()
    return jsonify({
        'movimentacoes': [m.to_dict() for m in movs],
        'emprestimos':   [e.to_dict() for e in loans]
    })

# ── MOVIMENTAÇÕES ────────────────────────────────────────────────

@bp.route('/api/movimentacoes', methods=['GET'])
@login_required
def api_listar_movimentacoes():
    equipamento_id = request.args.get('equipamento_id')
    tipo           = request.args.get('tipo')
    query          = Movimentacao.query.order_by(Movimentacao.criado_em.desc())
    if equipamento_id: query = query.filter_by(equipamento_id=int(equipamento_id))
    if tipo:           query = query.filter_by(tipo=tipo)
    return jsonify([m.to_dict() for m in query.limit(100).all()])

@bp.route('/api/movimentacoes', methods=['POST'])
@login_required
def api_criar_movimentacao():
    data = request.get_json()
    try:
        eq  = Equipamento.query.get_or_404(int(data['equipamento_id']))
        qtd = int(data['quantidade'])

        if data['tipo'] == 'entrada':
            eq.quantidade += qtd
        else:
            if eq.quantidade < qtd:
                return jsonify({'success': False, 'error': 'Quantidade insuficiente em estoque'}), 400
            eq.quantidade -= qtd

        mov = Movimentacao(
            equipamento_id = eq.id,
            tipo           = data['tipo'],
            quantidade     = qtd,
            motivo         = data.get('motivo', ''),
            responsavel    = data.get('responsavel', ''),
            observacoes    = data.get('observacoes', '')
        )
        db.session.add(mov)
        db.session.commit()
        return jsonify({'success': True, 'id': mov.id, 'quantidade_atual': eq.quantidade}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400