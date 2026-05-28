from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from app import db
from app.models import Emprestimo
from datetime import datetime

bp = Blueprint('relatorios', __name__)

@bp.route('/relatorios')
@login_required
def lista():
    return render_template('index.html')

@bp.route('/api/relatorios/mensal', methods=['GET'])
@login_required
def api_mensal():
    mes        = int(request.args.get('mes', datetime.now().month))
    ano        = int(request.args.get('ano', datetime.now().year))
    instituicao = request.args.get('instituicao')

    query = Emprestimo.query.filter(
        db.extract('month', Emprestimo.data_hora_entrega) == mes,
        db.extract('year',  Emprestimo.data_hora_entrega) == ano
    )

    if instituicao:
        query = query.filter_by(instituicao=instituicao)

    emprestimos = query.order_by(Emprestimo.data_hora_entrega).all()

    total      = len(emprestimos)
    devolvidos = 0
    atrasados  = 0

    por_equipamento = {}
    por_responsavel = {}
    por_turno       = {'manha': 0, 'noite': 0, 'outro': 0}
    por_instituicao = {'UniFECAF': 0, 'ColégioSER': 0}

    for e in emprestimos:
        status = e.calcular_status()

        if status == 'devolvido':
            devolvidos += 1
        elif status == 'em_atraso':
            atrasados += 1

        nome_eq = e.equipamento.nome if e.equipamento else 'Desconhecido'
        por_equipamento[nome_eq] = por_equipamento.get(nome_eq, 0) + 1
        por_responsavel[e.responsavel] = por_responsavel.get(e.responsavel, 0) + 1
        por_turno[e.turno] = por_turno.get(e.turno, 0) + 1
        por_instituicao[e.instituicao] = por_instituicao.get(e.instituicao, 0) + 1

    nao_devolvidos = total - devolvidos
    nao_devolvidos_lista = [
        e.to_dict() for e in emprestimos if e.calcular_status() != 'devolvido'
    ]

    return jsonify({
        'mes':               mes,
        'ano':               ano,
        'total':             total,
        'devolvidos':        devolvidos,
        'nao_devolvidos':    nao_devolvidos,
        'atrasados':         atrasados,
        'por_equipamento':   por_equipamento,
        'por_responsavel':   por_responsavel,
        'por_turno':         por_turno,
        'por_instituicao':   por_instituicao,
        'nao_devolvidos_lista': nao_devolvidos_lista,
        'todos':             [e.to_dict() for e in emprestimos]
    })

@bp.route('/api/relatorios/historico_mensal', methods=['GET'])
@login_required
def api_historico():
    ano = int(request.args.get('ano', datetime.now().year))
    resultado = []
    for mes in range(1, 13):
        count = Emprestimo.query.filter(
            db.extract('month', Emprestimo.data_hora_entrega) == mes,
            db.extract('year',  Emprestimo.data_hora_entrega) == ano
        ).count()
        resultado.append({'mes': mes, 'total': count})
    return jsonify(resultado)