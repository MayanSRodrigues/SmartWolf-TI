import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr
from datetime import datetime
import re


def decodificar_header(valor):
    """Decodifica headers de e-mail que podem estar em base64 ou quoted-printable."""
    if not valor:
        return ''
    partes = decode_header(valor)
    resultado = []
    for parte, encoding in partes:
        if isinstance(parte, bytes):
            try:
                resultado.append(parte.decode(encoding or 'utf-8', errors='replace'))
            except Exception:
                resultado.append(parte.decode('latin-1', errors='replace'))
        else:
            resultado.append(str(parte))
    return ' '.join(resultado).strip()


def extrair_texto(msg):
    """Extrai o texto do corpo do e-mail."""
    corpo = ''
    if msg.is_multipart():
        for parte in msg.walk():
            tipo = parte.get_content_type()
            disposicao = str(parte.get('Content-Disposition', ''))
            if tipo == 'text/plain' and 'attachment' not in disposicao:
                try:
                    charset = parte.get_content_charset() or 'utf-8'
                    corpo = parte.get_payload(decode=True).decode(charset, errors='replace')
                    break
                except Exception:
                    continue
    else:
        try:
            charset = msg.get_content_charset() or 'utf-8'
            corpo = msg.get_payload(decode=True).decode(charset, errors='replace')
        except Exception:
            corpo = ''
    return corpo.strip()


def extrair_anexos(msg):
    """Extrai anexos do e-mail como lista de dicts com nome, tipo e dados em bytes."""
    anexos = []
    if msg.is_multipart():
        for parte in msg.walk():
            disposicao = str(parte.get('Content-Disposition', ''))
            if 'attachment' in disposicao:
                nome = parte.get_filename()
                if nome:
                    nome = decodificar_header(nome)
                    dados = parte.get_payload(decode=True)
                    tipo  = parte.get_content_type()
                    if dados:
                        anexos.append({'nome': nome, 'tipo': tipo, 'dados': dados})
    return anexos


def ler_emails_novos(app):
    """
    Conecta ao IMAP, lê e-mails não lidos e cria chamados de suporte.
    Deve ser chamado pelo scheduler.
    """
    from app import db
    from app.models.suporte import ChamadoSuporte, AnexoSuporte

    cfg = app.config
    servidor = cfg.get('IMAP_SERVER')
    porta    = cfg.get('IMAP_PORT', 993)
    email_c  = cfg.get('IMAP_EMAIL')
    senha    = cfg.get('IMAP_SENHA')

    if not all([servidor, email_c, senha]):
        print('⚠️ IMAP não configurado — pulando leitura de e-mails.')
        return

    try:
        mail = imaplib.IMAP4_SSL(servidor, porta)
        mail.login(email_c, senha)
        mail.select('INBOX')

        # Busca e-mails não lidos
        status, mensagens = mail.search(None, 'UNSEEN')
        if status != 'OK':
            mail.logout()
            return

        ids = mensagens[0].split()
        if not ids or ids == [b'']:
            mail.logout()
            return

        print(f'📧 {len(ids)} e-mail(s) novo(s) encontrado(s).')

        with app.app_context():
            for num in ids:
                try:
                    _, dados = mail.fetch(num, '(RFC822)')
                    msg_raw  = dados[0][1]
                    msg      = email.message_from_bytes(msg_raw)

                    assunto  = decodificar_header(msg.get('Subject', 'Sem assunto'))
                    de       = msg.get('From', '')
                    nome_de, email_de = parseaddr(de)
                    nome_de  = decodificar_header(nome_de) or email_de
                    corpo    = extrair_texto(msg)
                    anexos   = extrair_anexos(msg)

                    # Limpa o corpo de assinaturas longas
                    linhas = corpo.split('\n')
                    linhas_limpas = []
                    for linha in linhas:
                        if linha.strip().startswith('--'):
                            break
                        linhas_limpas.append(linha)
                    corpo_limpo = '\n'.join(linhas_limpas).strip() or corpo[:2000]

                    # Cria o chamado
                    chamado = ChamadoSuporte(
                        titulo            = assunto[:200],
                        descricao         = corpo_limpo or '(sem descrição)',
                        solicitante_nome  = nome_de or 'Desconhecido',
                        solicitante_email = email_de or '',
                        tipo              = 'requisicao',
                        prioridade        = 'media',
                        status            = 'aberto',
                    )
                    db.session.add(chamado)
                    db.session.flush()

                    # Salva anexos
                    for a in anexos:
                        db.session.add(AnexoSuporte(
                            chamado_id   = chamado.id,
                            nome_arquivo = a['nome'],
                            tipo_mime    = a['tipo'],
                            dados        = a['dados'],
                            tamanho      = len(a['dados'])
                        ))

                    db.session.commit()
                    print(f'✅ Chamado #{chamado.id} criado: {assunto}')

                    # Marca como lido
                    mail.store(num, '+FLAGS', '\\Seen')

                except Exception as e:
                    db.session.rollback()
                    print(f'❌ Erro ao processar e-mail: {e}')

        mail.logout()

    except Exception as e:
        print(f'❌ Erro ao conectar ao IMAP: {e}')