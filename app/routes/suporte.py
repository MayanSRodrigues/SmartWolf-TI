from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models import Usuario
from app.models.suporte import ChamadoSuporte, ComentarioSuporte, AnexoSuporte
from datetime import datetime
import io

bp = Blueprint('suporte', __name__)


# ── DASHBOARD ────────────────────────────────────────────────────

@bp.route('/api/suporte/resumo', methods=['GET'])
@login_required
def api_suporte_resumo():
    todos = ChamadoSuporte.query.all()
    return jsonify({
        'total':       len(todos),
        'aberto':      sum(1 for c in todos if c.status == 'aberto'),
        'em_andamento':sum(1 for c in todos if c.status == 'em_andamento'),
        'pendente':    sum(1 for c in todos if c.status == 'pendente'),
        'resolvido':   sum(1 for c in todos if c.status == 'resolvido'),
        'fechado':     sum(1 for c in todos if c.status == 'fechado'),
        'critica':     sum(1 for c in todos if c.prioridade == 'critica' and c.status not in ('resolvido','fechado')),
        'alta':        sum(1 for c in todos if c.prioridade == 'alta'    and c.status not in ('resolvido','fechado')),
    })


# ── LISTAGEM ─────────────────────────────────────────────────────

@bp.route('/api/suporte/chamados', methods=['GET'])
@login_required
def api_suporte_listar():
    status     = request.args.get('status')
    prioridade = request.args.get('prioridade')
    tipo       = request.args.get('tipo')
    busca      = request.args.get('busca', '').strip()
    meu        = request.args.get('meu')  # chamados do técnico logado

    query = ChamadoSuporte.query

    if status:     query = query.filter_by(status=status)
    if prioridade: query = query.filter_by(prioridade=prioridade)
    if tipo:       query = query.filter_by(tipo=tipo)
    if meu == 'true':
        query = query.filter(
            (ChamadoSuporte.tecnico_id == current_user.id) |
            (ChamadoSuporte.tecnicos.any(id=current_user.id))
        )
    if busca:
        query = query.filter(
            ChamadoSuporte.titulo.ilike(f'%{busca}%') |
            ChamadoSuporte.solicitante_nome.ilike(f'%{busca}%') |
            ChamadoSuporte.solicitante_email.ilike(f'%{busca}%')
        )

    chamados = query.order_by(
        ChamadoSuporte.criado_em.desc()
    ).all()

    return jsonify([c.to_dict(resumido=True) for c in chamados])


# ── DETALHES ─────────────────────────────────────────────────────

@bp.route('/api/suporte/chamados/<int:id>', methods=['GET'])
@login_required
def api_suporte_detalhe(id):
    c = ChamadoSuporte.query.get_or_404(id)
    return jsonify(c.to_dict())


# ── CRIAR ────────────────────────────────────────────────────────

@bp.route('/api/suporte/chamados', methods=['POST'])
@login_required
def api_suporte_criar():
    data = request.get_json()
    try:
        c = ChamadoSuporte(
            titulo            = data['titulo'],
            descricao         = data['descricao'],
            solicitante_nome  = data['solicitante_nome'],
            solicitante_email = data['solicitante_email'],
            solicitante_setor = data.get('solicitante_setor', ''),
            tipo              = data.get('tipo', 'requisicao'),
            prioridade        = data.get('prioridade', 'media'),
            status            = data.get('status', 'aberto'),
            instituicao       = data.get('instituicao') or None,
            tecnico_id        = int(data['tecnico_id']) if data.get('tecnico_id') else None,
            aberto_por_id     = current_user.id,
        )

        # Técnicos adicionais
        ids_tecnicos = data.get('tecnicos_ids', [])
        if ids_tecnicos:
            tecnicos = Usuario.query.filter(Usuario.id.in_(ids_tecnicos)).all()
            c.tecnicos = tecnicos

        db.session.add(c)
        db.session.flush()  # gera o ID

        # Comentário inicial automático
        db.session.add(ComentarioSuporte(
            chamado_id = c.id,
            autor_id   = current_user.id,
            texto      = f'Chamado aberto por {current_user.nome}.',
            interno    = True
        ))

        db.session.commit()
        return jsonify({'success': True, 'id': c.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


# ── EDITAR ───────────────────────────────────────────────────────

@bp.route('/api/suporte/chamados/<int:id>', methods=['PUT'])
@login_required
def api_suporte_editar(id):
    c    = ChamadoSuporte.query.get_or_404(id)
    data = request.get_json()
    try:
        status_anterior = c.status

        c.titulo            = data.get('titulo',            c.titulo)
        c.descricao         = data.get('descricao',         c.descricao)
        c.solicitante_nome  = data.get('solicitante_nome',  c.solicitante_nome)
        c.solicitante_email = data.get('solicitante_email', c.solicitante_email)
        c.solicitante_setor = data.get('solicitante_setor', c.solicitante_setor)
        c.tipo              = data.get('tipo',              c.tipo)
        c.prioridade        = data.get('prioridade',        c.prioridade)
        c.status            = data.get('status',            c.status)
        c.instituicao       = data.get('instituicao',       c.instituicao) or None
        c.tecnico_id        = int(data['tecnico_id']) if data.get('tecnico_id') else c.tecnico_id
        c.atualizado_em     = datetime.utcnow()

        # Datas automáticas de resolução/fechamento
        if c.status == 'resolvido' and not c.resolvido_em:
            c.resolvido_em = datetime.utcnow()
        if c.status == 'fechado' and not c.fechado_em:
            c.fechado_em = datetime.utcnow()

        # Técnicos adicionais
        if 'tecnicos_ids' in data:
            tecnicos = Usuario.query.filter(Usuario.id.in_(data['tecnicos_ids'])).all()
            c.tecnicos = tecnicos

        # Log automático de mudança de status
        if status_anterior != c.status:
            labels = {
                'aberto': 'Aberto', 'em_andamento': 'Em Andamento',
                'pendente': 'Pendente', 'resolvido': 'Resolvido', 'fechado': 'Fechado'
            }
            db.session.add(ComentarioSuporte(
                chamado_id = c.id,
                autor_id   = current_user.id,
                texto      = f'Status alterado de **{labels.get(status_anterior, status_anterior)}** para **{labels.get(c.status, c.status)}**.',
                interno    = True
            ))

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


# ── COMENTÁRIOS ──────────────────────────────────────────────────

@bp.route('/api/suporte/chamados/<int:id>/comentarios', methods=['POST'])
@login_required
def api_suporte_comentar(id):
    c    = ChamadoSuporte.query.get_or_404(id)
    data = request.get_json()
    try:
        comentario = ComentarioSuporte(
            chamado_id = c.id,
            autor_id   = current_user.id,
            texto      = data['texto'],
            interno    = data.get('interno', False)
        )
        db.session.add(comentario)
        db.session.flush()

        # Anexos em base64
        for anexo_data in data.get('anexos', []):
            import base64
            conteudo = base64.b64decode(anexo_data['dados'])
            db.session.add(AnexoSuporte(
                chamado_id    = c.id,
                comentario_id = comentario.id,
                nome_arquivo  = anexo_data['nome'],
                tipo_mime     = anexo_data.get('tipo', 'application/octet-stream'),
                dados         = conteudo,
                tamanho       = len(conteudo)
            ))

        # Atualiza timestamp do chamado
        c.atualizado_em = datetime.utcnow()
        if c.status == 'aberto':
            c.status = 'em_andamento'

        db.session.commit()
        return jsonify({'success': True, 'comentario': comentario.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


# ── ANEXOS ───────────────────────────────────────────────────────

@bp.route('/api/suporte/chamados/<int:id>/anexos', methods=['POST'])
@login_required
def api_suporte_anexar(id):
    c = ChamadoSuporte.query.get_or_404(id)
    try:
        import base64
        data = request.get_json()
        anexos_criados = []
        for anexo_data in data.get('anexos', []):
            conteudo = base64.b64decode(anexo_data['dados'])
            anexo = AnexoSuporte(
                chamado_id   = c.id,
                nome_arquivo = anexo_data['nome'],
                tipo_mime    = anexo_data.get('tipo', 'application/octet-stream'),
                dados        = conteudo,
                tamanho      = len(conteudo)
            )
            db.session.add(anexo)
            db.session.flush()
            anexos_criados.append(anexo.to_dict())

        db.session.commit()
        return jsonify({'success': True, 'anexos': anexos_criados}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/api/suporte/anexos/<int:id>', methods=['GET'])
@login_required
def api_suporte_baixar_anexo(id):
    anexo = AnexoSuporte.query.get_or_404(id)
    return send_file(
        io.BytesIO(anexo.dados),
        mimetype=anexo.tipo_mime,
        as_attachment=True,
        download_name=anexo.nome_arquivo
    )


# ── ATRIBUIR TÉCNICO ─────────────────────────────────────────────

@bp.route('/api/suporte/chamados/<int:id>/atribuir', methods=['POST'])
@login_required
def api_suporte_atribuir(id):
    c    = ChamadoSuporte.query.get_or_404(id)
    data = request.get_json()
    try:
        tecnico_id = data.get('tecnico_id')
        if tecnico_id:
            tecnico = Usuario.query.get_or_404(int(tecnico_id))
            c.tecnico_id = tecnico.id
            # Adiciona à lista de técnicos se não estiver
            if tecnico not in c.tecnicos:
                c.tecnicos.append(tecnico)
            if c.status == 'aberto':
                c.status = 'em_andamento'
            db.session.add(ComentarioSuporte(
                chamado_id = c.id,
                autor_id   = current_user.id,
                texto      = f'Chamado atribuído para **{tecnico.nome}**.',
                interno    = True
            ))

        # Adicionar técnico extra
        extra_id = data.get('adicionar_tecnico_id')
        if extra_id:
            extra = Usuario.query.get_or_404(int(extra_id))
            if extra not in c.tecnicos:
                c.tecnicos.append(extra)
                db.session.add(ComentarioSuporte(
                    chamado_id = c.id,
                    autor_id   = current_user.id,
                    texto      = f'**{extra.nome}** adicionado ao chamado.',
                    interno    = True
                ))

        c.atualizado_em = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


# ── PEGAR CHAMADO (técnico assume) ───────────────────────────────

@bp.route('/api/suporte/chamados/<int:id>/pegar', methods=['POST'])
@login_required
def api_suporte_pegar(id):
    c = ChamadoSuporte.query.get_or_404(id)
    try:
        c.tecnico_id = current_user.id
        if current_user not in c.tecnicos:
            c.tecnicos.append(current_user)
        if c.status == 'aberto':
            c.status = 'em_andamento'
        c.atualizado_em = datetime.utcnow()
        db.session.add(ComentarioSuporte(
            chamado_id = c.id,
            autor_id   = current_user.id,
            texto      = f'**{current_user.nome}** assumiu este chamado.',
            interno    = True
        ))
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


# ── DELETAR ──────────────────────────────────────────────────────

@bp.route('/api/suporte/chamados/limpar', methods=['POST'])
@login_required
def api_suporte_limpar():
    if not current_user.is_admin():
        return jsonify({'error': 'Sem permissão'}), 403
    primeiro = ChamadoSuporte.query.order_by(ChamadoSuporte.id.asc()).first()
    if not primeiro:
        return jsonify({'message': 'Nenhum chamado encontrado'})
    duplicados = ChamadoSuporte.query.filter(ChamadoSuporte.id != primeiro.id).all()
    for c in duplicados:
        db.session.delete(c)
    db.session.commit()
    return jsonify({'success': True, 'message': f'{len(duplicados)} chamados removidos, mantido #{primeiro.id}'})