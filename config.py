import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Segurança
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-secreta-ti-2024'

    # Banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:SUA_SENHA@localhost/emprestimos_ti?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Regra de atraso: 1 hora após fim do turno
    ATRASO_TOLERANCIA_HORAS = 1

    # Horários dos turnos
    TURNO_MANHA_INICIO = '07:15'
    TURNO_MANHA_FIM    = '10:00'
    TURNO_NOITE_INICIO = '19:15'
    TURNO_NOITE_FIM    = '22:00'

    # Configurações de e-mail
    MAIL_SERVER   = os.environ.get('MAIL_SERVER')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_FROM     = os.environ.get('MAIL_FROM')

    # Fuso horário
    TIMEZONE = 'America/Sao_Paulo'

    # Timeout de inatividade em minutos (ajuste aqui quando necessário)
    SESSION_TIMEOUT_MINUTOS = 60