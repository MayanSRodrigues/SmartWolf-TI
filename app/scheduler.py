from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

scheduler = BackgroundScheduler(timezone='America/Sao_Paulo')

def iniciar_scheduler(app):
    """Inicia o agendador de tarefas com o contexto do Flask."""

    def verificar_lembretes():
        """Roda a cada 5 minutos — verifica lembretes e atrasos."""
        with app.app_context():
            from app.models import Emprestimo
            from app import db
            from app.email import (
                enviar_email,
                template_lembrete,
                template_atraso
            )

            agora = datetime.now()
            em_aberto = Emprestimo.query.filter(
                Emprestimo.data_hora_devolucao_real == None
            ).all()

            for e in em_aberto:
                tempo_restante = e.data_hora_devolucao_prevista - agora
                minutos_restantes = tempo_restante.total_seconds() / 60

                if 28 <= minutos_restantes <= 32 and not e.lembrete_enviado:
                    html = template_lembrete(
                        responsavel        = e.responsavel,
                        equipamento        = e.equipamento.nome,
                        patrimonio         = e.equipamento.patrimonio,
                        devolucao_prevista = e.data_hora_devolucao_prevista.strftime('%d/%m/%Y %H:%M'),
                        instituicao        = e.instituicao
                    )
                    enviado = enviar_email(
                        destinatario = e.email,
                        assunto      = f"⏰ Lembrete: devolva o {e.equipamento.nome} em 30 minutos",
                        corpo_html   = html
                    )
                    if enviado:
                        e.lembrete_enviado = True
                        db.session.commit()

                limite_atraso = e.data_hora_devolucao_prevista + timedelta(hours=1)
                if agora > limite_atraso and not e.aviso_atraso_enviado:
                    html = template_atraso(
                        responsavel        = e.responsavel,
                        equipamento        = e.equipamento.nome,
                        patrimonio         = e.equipamento.patrimonio,
                        devolucao_prevista = e.data_hora_devolucao_prevista.strftime('%d/%m/%Y %H:%M'),
                        instituicao        = e.instituicao
                    )
                    enviado = enviar_email(
                        destinatario = e.email,
                        assunto      = f"⚠️ ATRASO: {e.equipamento.nome} não foi devolvido",
                        corpo_html   = html
                    )
                    if enviado:
                        e.aviso_atraso_enviado = True
                        e.status = 'em_atraso'
                        db.session.commit()

    def verificar_emails():
        """Roda a cada 5 minutos — lê e-mails novos e cria chamados."""
        try:
            from app.email_reader import ler_emails_novos
            ler_emails_novos(app)
        except Exception as e:
            print(f'❌ Erro no leitor de e-mails: {e}')

    scheduler.add_job(
        func             = verificar_lembretes,
        trigger          = 'interval',
        minutes          = 5,
        id               = 'verificar_lembretes',
        replace_existing = True
    )

    scheduler.add_job(
        func             = verificar_emails,
        trigger          = 'interval',
        minutes          = 5,
        id               = 'verificar_emails',
        replace_existing = True
    )

    if not scheduler.running:
        scheduler.start()
        print("✅ Agendador iniciado — lembretes e e-mails ativos!")