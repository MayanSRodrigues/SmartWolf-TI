from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Chamado, Emprestimo, Equipamento
from datetime import datetime

bp = Blueprint('chamados', __name__)

@bp.route('/api/chamados', methods=['GET'])
@login_required
def api_listar():
    status_filtro  = request.args.get('status')
    instituicao    = request.args.get('instituicao')

    query = Chamado.query.order_by(Chamado.data_hora_entrega.desc())

    if instituicao:
        query = query.filter_by(instituicao=instituicao)

    chamados = query.all()

    resultado = []
    for c in chamados:
        novo_status = c.calcular_status()
        if c.status != novo_status:
            c.status = novo_status
            db.session.commit()
        d = c.to_dict()
        if status_filtro and d['status'] != status_filtro:
            continue
        resultado.append(d)

    return jsonify(resultado)

@bp.route('/api/chamados', methods=['POST'])
@login_required
def api_criar():
    data = request.get_json()
    try:
        fmt = '%Y-%m-%dT%H:%M'
        chamado = Chamado(
            responsavel                  = data['responsavel'],
            email                        = data['email'],
            local_uso                    = data['local_uso'],
            instituicao                  = data['instituicao'],
            turno                        = data.get('turno', 'outro'),
            data_hora_entrega            = datetime.strptime(data['data_hora_entrega'], fmt),
            data_hora_devolucao_prevista = datetime.strptime(data['data_hora_devolucao_prevista'], fmt),
            observacoes                  = data.get('observacoes', '')
        )
        db.session.add(chamado)
        db.session.flush()  # Gera o ID do chamado

        # Cria um empréstimo para cada equipamento
        # Cria um empréstimo para cada equipamento
        equipamentos_ids = data.get('equipamentos_ids', [])
        for eq_id in equipamentos_ids:
            # Verifica se equipamento já está emprestado
            emprestimo_ativo = Emprestimo.query.filter(
                Emprestimo.equipamento_id == int(eq_id),
                Emprestimo.status.in_(['ativo', 'em_atraso']),
                Emprestimo.data_hora_devolucao_real == None
            ).first()
            if emprestimo_ativo:
                eq = Equipamento.query.get(int(eq_id))
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Equipamento "{eq.nome} — {eq.patrimonio}" já está emprestado!'
                }), 400

            emp = Emprestimo(
                equipamento_id               = int(eq_id),
                chamado_id                   = chamado.id,
                responsavel                  = chamado.responsavel,
                email                        = chamado.email,
                local_uso                    = chamado.local_uso,
                instituicao                  = chamado.instituicao,
                turno                        = chamado.turno,
                data_hora_entrega            = chamado.data_hora_entrega,
                data_hora_devolucao_prevista = chamado.data_hora_devolucao_prevista,
                observacoes                  = chamado.observacoes
            )
            db.session.add(emp)

        db.session.commit()

        # Envia e-mail de confirmação
        try:
            from app.email import enviar_email, template_confirmacao
            equips = Equipamento.query.filter(
                Equipamento.id.in_([int(i) for i in equipamentos_ids])
            ).all()
            nomes = ', '.join([e.nome for e in equips])
            html = template_confirmacao(
                responsavel        = chamado.responsavel,
                equipamento        = nomes,
                patrimonio         = ', '.join([e.patrimonio or '—' for e in equips]),
                local              = chamado.local_uso,
                instituicao        = chamado.instituicao,
                entrega            = chamado.data_hora_entrega.strftime('%d/%m/%Y %H:%M'),
                devolucao_prevista = chamado.data_hora_devolucao_prevista.strftime('%d/%m/%Y %H:%M')
            )
            enviar_email(
                destinatario = chamado.email,
                assunto      = f"📋 Chamado #{chamado.id} registrado — {nomes}",
                corpo_html   = html
            )
        except Exception as ex:
            print(f"Aviso: e-mail não enviado: {ex}")

        return jsonify({'success': True, 'id': chamado.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/chamados/<int:id>', methods=['GET'])
@login_required
def api_get(id):
    chamado = Chamado.query.get_or_404(id)
    return jsonify(chamado.to_dict())

@bp.route('/api/chamados/<int:id>/adicionar_equipamento', methods=['POST'])
@login_required
def api_adicionar_equipamento(id):
    chamado = Chamado.query.get_or_404(id)
    data    = request.get_json()
    try:
        eq_id = int(data['equipamento_id'])

        # Verifica se equipamento já está emprestado
        emprestimo_ativo = Emprestimo.query.filter(
            Emprestimo.equipamento_id == eq_id,
            Emprestimo.status.in_(['ativo', 'em_atraso']),
            Emprestimo.data_hora_devolucao_real == None
        ).first()
        if emprestimo_ativo:
            eq = Equipamento.query.get(eq_id)
            return jsonify({
                'success': False,
                'error': f'Equipamento "{eq.nome} — {eq.patrimonio}" já está emprestado!'
            }), 400

        emp = Emprestimo(
            equipamento_id               = eq_id,
            chamado_id                   = chamado.id,
            responsavel                  = chamado.responsavel,
            email                        = chamado.email,
            local_uso                    = chamado.local_uso,
            instituicao                  = chamado.instituicao,
            turno                        = chamado.turno,
            data_hora_entrega            = chamado.data_hora_entrega,
            data_hora_devolucao_prevista = chamado.data_hora_devolucao_prevista,
            observacoes                  = chamado.observacoes
        )
        db.session.add(emp)
        db.session.commit()
        return jsonify({'success': True, 'id': emp.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/chamados/<int:id>/devolver_tudo', methods=['POST'])
@login_required
def api_devolver_tudo(id):
    chamado = Chamado.query.get_or_404(id)
    agora   = datetime.now()
    for emp in chamado.itens:
        if not emp.data_hora_devolucao_real:
            emp.data_hora_devolucao_real = agora
            emp.status = 'devolvido'
    chamado.status = 'devolvido'
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/chamados/<int:id>', methods=['DELETE'])
@login_required
def api_deletar(id):
    chamado = Chamado.query.get_or_404(id)
    for emp in chamado.itens:
        db.session.delete(emp)
    db.session.delete(chamado)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/chamados/dashboard', methods=['GET'])
@login_required
def api_dashboard():
    todos      = Chamado.query.all()
    total      = len(todos)
    ativos     = 0
    atrasados  = 0
    devolvidos = 0

    for c in todos:
        s = c.calcular_status()
        if s == 'devolvido':
            devolvidos += 1
        elif s == 'em_atraso':
            atrasados += 1
        else:
            ativos += 1

    return jsonify({
        'total':      total,
        'ativos':     ativos,
        'atrasados':  atrasados,
        'devolvidos': devolvidos
    })