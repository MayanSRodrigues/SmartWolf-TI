import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app

def enviar_email(destinatario, assunto, corpo_html):
    """Envia um e-mail HTML para o destinatário."""
    try:
        server   = current_app.config['MAIL_SERVER']
        port     = current_app.config['MAIL_PORT']
        username = current_app.config['MAIL_USERNAME']
        password = current_app.config['MAIL_PASSWORD']
        remetente = current_app.config['MAIL_FROM']

        if not all([server, port, username, password, remetente]):
            print("⚠️  Configurações de e-mail incompletas no .env")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = assunto
        msg['From']    = f"TI UniFECAF & ColégioSER <{remetente}>"
        msg['To']      = destinatario

        msg.attach(MIMEText(corpo_html, 'html', 'utf-8'))

        with smtplib.SMTP(server, port) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(username, password)
            smtp.sendmail(remetente, destinatario, msg.as_string())

        print(f"✅ E-mail enviado para {destinatario} — {assunto}")
        return True

    except Exception as e:
        print(f"❌ Erro ao enviar e-mail para {destinatario}: {e}")
        return False


def template_confirmacao(responsavel, equipamento, patrimonio, local, instituicao, entrega, devolucao_prevista):
    """Template de e-mail de confirmação de empréstimo."""
    cor = '#003F8A' if instituicao == 'UniFECAF' else '#007A3D'
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f5f5f5;padding:20px">
      <div style="background:{cor};padding:24px;border-radius:8px 8px 0 0;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:20px">📋 Empréstimo Registrado</h1>
        <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;font-size:14px">{instituicao} — Departamento de TI</p>
      </div>
      <div style="background:#fff;padding:28px;border-radius:0 0 8px 8px">
        <p style="font-size:15px;color:#333">Olá, <strong>{responsavel}</strong>!</p>
        <p style="font-size:14px;color:#555">Seu empréstimo foi registrado com sucesso. Confira os detalhes:</p>

        <div style="background:#f8f8f8;border-left:4px solid {cor};padding:16px;border-radius:4px;margin:20px 0">
          <table style="width:100%;font-size:14px;color:#333">
            <tr><td style="padding:6px 0;color:#888">Equipamento</td>
                <td style="padding:6px 0"><strong>{equipamento}</strong></td></tr>
            <tr><td style="padding:6px 0;color:#888">Patrimônio</td>
                <td style="padding:6px 0">{patrimonio}</td></tr>
            <tr><td style="padding:6px 0;color:#888">Local de Uso</td>
                <td style="padding:6px 0">{local}</td></tr>
            <tr><td style="padding:6px 0;color:#888">Retirada</td>
                <td style="padding:6px 0">{entrega}</td></tr>
            <tr><td style="padding:6px 0;color:#888">Devolução Prevista</td>
                <td style="padding:6px 0"><strong>{devolucao_prevista}</strong></td></tr>
          </table>
        </div>

        <p style="font-size:13px;color:#888;margin-top:20px">
          Por favor, devolva o equipamento até o horário previsto.<br>
          Em caso de dúvidas, entre em contato com o Departamento de TI.
        </p>
      </div>
      <p style="text-align:center;font-size:11px;color:#aaa;margin-top:12px">
        Este é um e-mail automático — TI {instituicao}
      </p>
    </div>
    """


def template_lembrete(responsavel, equipamento, patrimonio, devolucao_prevista, instituicao):
    """Template de lembrete 30 minutos antes da devolução."""
    cor = '#003F8A' if instituicao == 'UniFECAF' else '#007A3D'
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f5f5f5;padding:20px">
      <div style="background:#F47920;padding:24px;border-radius:8px 8px 0 0;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:20px">⏰ Lembrete de Devolução</h1>
        <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;font-size:14px">{instituicao} — Departamento de TI</p>
      </div>
      <div style="background:#fff;padding:28px;border-radius:0 0 8px 8px">
        <p style="font-size:15px;color:#333">Olá, <strong>{responsavel}</strong>!</p>
        <p style="font-size:14px;color:#555">
          Este é um lembrete de que o equipamento abaixo deve ser devolvido em <strong>30 minutos</strong>:
        </p>

        <div style="background:#fff8f0;border-left:4px solid #F47920;padding:16px;border-radius:4px;margin:20px 0">
          <table style="width:100%;font-size:14px;color:#333">
            <tr><td style="padding:6px 0;color:#888">Equipamento</td>
                <td style="padding:6px 0"><strong>{equipamento}</strong></td></tr>
            <tr><td style="padding:6px 0;color:#888">Patrimônio</td>
                <td style="padding:6px 0">{patrimonio}</td></tr>
            <tr><td style="padding:6px 0;color:#888">Devolução Prevista</td>
                <td style="padding:6px 0"><strong style="color:#F47920">{devolucao_prevista}</strong></td></tr>
          </table>
        </div>

        <p style="font-size:13px;color:#888">
          Por favor, devolva o equipamento ao Departamento de TI no horário previsto.
        </p>
      </div>
      <p style="text-align:center;font-size:11px;color:#aaa;margin-top:12px">
        Este é um e-mail automático — TI {instituicao}
      </p>
    </div>
    """


def template_atraso(responsavel, equipamento, patrimonio, devolucao_prevista, instituicao):
    """Template de notificação de atraso."""
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f5f5f5;padding:20px">
      <div style="background:#c0392b;padding:24px;border-radius:8px 8px 0 0;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:20px">⚠️ Equipamento em Atraso</h1>
        <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;font-size:14px">{instituicao} — Departamento de TI</p>
      </div>
      <div style="background:#fff;padding:28px;border-radius:0 0 8px 8px">
        <p style="font-size:15px;color:#333">Olá, <strong>{responsavel}</strong>!</p>
        <p style="font-size:14px;color:#c0392b">
          <strong>O prazo de devolução foi ultrapassado.</strong> Por favor, devolva o equipamento imediatamente.
        </p>

        <div style="background:#fff5f5;border-left:4px solid #c0392b;padding:16px;border-radius:4px;margin:20px 0">
          <table style="width:100%;font-size:14px;color:#333">
            <tr><td style="padding:6px 0;color:#888">Equipamento</td>
                <td style="padding:6px 0"><strong>{equipamento}</strong></td></tr>
            <tr><td style="padding:6px 0;color:#888">Patrimônio</td>
                <td style="padding:6px 0">{patrimonio}</td></tr>
            <tr><td style="padding:6px 0;color:#888">Devolveu deveria ser até</td>
                <td style="padding:6px 0"><strong style="color:#c0392b">{devolucao_prevista}</strong></td></tr>
          </table>
        </div>

        <p style="font-size:13px;color:#888">
          Dirija-se ao Departamento de TI para realizar a devolução.<br>
          Em caso de dúvidas, entre em contato conosco.
        </p>
      </div>
      <p style="text-align:center;font-size:11px;color:#aaa;margin-top:12px">
        Este é um e-mail automático — TI {instituicao}
      </p>
    </div>
    """