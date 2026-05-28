from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from app import db
from app.models import Emprestimo, Equipamento
from datetime import datetime

bp = Blueprint('emprestimos', __name__)

@bp.route('/')
@login_required
def index():
    return render_template('index.html')

@bp.route('/emprestimos')
@login_required
def lista():
    return render_template('index.html')

@bp.route('/api/emprestimos', methods=['GET'])
@login_required
def api_listar():
    status_filtro  = request.args.get('status')
    instituicao    = request.args.get('instituicao')
    mes            = request.args.get('mes')
    ano            = request.args.get('ano')

    query = Emprestimo.query.order_by(Emprestimo.data_hora_entrega.desc())

    if instituicao:
        query = query.filter_by(instituicao=instituicao)
    if mes and ano:
        query = query.filter(
            db.extract('month', Emprestimo.data_hora_entrega) == int(mes),
            db.extract('year',  Emprestimo.data_hora_entrega) == int(ano)
        )

    emprestimos = query.all()

    resultado = []
    for e in emprestimos:
        novo_status = e.calcular_status()
        if e.status != novo_status:
            e.status = novo_status
            db.session.commit()
        d = e.to_dict()
        if status_filtro and d['status'] != status_filtro:
            continue
        resultado.append(d)

    return jsonify(resultado)

@bp.route('/api/emprestimos', methods=['POST'])
@login_required
def api_criar():
    data = request.get_json()
    try:
        fmt = '%Y-%m-%dT%H:%M'
        emp = Emprestimo(
            equipamento_id               = int(data['equipamento_id']),
            responsavel                  = data['responsavel'],
            email                        = data['email'],
            local_uso                    = data['local_uso'],
            instituicao                  = data['instituicao'],
            turno                        = data.get('turno', 'outro'),
            data_hora_entrega            = datetime.strptime(data['data_hora_entrega'], fmt),
            data_hora_devolucao_prevista = datetime.strptime(data['data_hora_devolucao_prevista'], fmt),
            observacoes                  = data.get('observacoes', '')
        )
        db.session.add(emp)
        db.session.commit()

        # Envia e-mail de confirmação
        try:
            from app.email import enviar_email, template_confirmacao
            html = template_confirmacao(
                responsavel        = emp.responsavel,
                equipamento        = emp.equipamento.nome,
                patrimonio         = emp.equipamento.patrimonio,
                local              = emp.local_uso,
                instituicao        = emp.instituicao,
                entrega            = emp.data_hora_entrega.strftime('%d/%m/%Y %H:%M'),
                devolucao_prevista = emp.data_hora_devolucao_prevista.strftime('%d/%m/%Y %H:%M')
            )
            enviar_email(
                destinatario = emp.email,
                assunto      = f"📋 Empréstimo registrado: {emp.equipamento.nome}",
                corpo_html   = html
            )
        except Exception as ex:
            print(f"Aviso: e-mail de confirmação não enviado: {ex}")

        return jsonify({'success': True, 'id': emp.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/emprestimos/<int:id>/devolver', methods=['POST'])
@login_required
def api_devolver(id):
    emp = Emprestimo.query.get_or_404(id)
    emp.data_hora_devolucao_real = datetime.now()
    emp.status = 'devolvido'
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/emprestimos/<int:id>', methods=['DELETE'])
@login_required
def api_deletar(id):
    emp = Emprestimo.query.get_or_404(id)
    db.session.delete(emp)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/dashboard', methods=['GET'])
@login_required
def api_dashboard():
    todos = Emprestimo.query.all()
    total     = len(todos)
    ativos    = 0
    atrasados = 0
    devolvidos = 0

    for e in todos:
        s = e.calcular_status()
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