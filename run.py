from app import create_app, db
from app.models import Equipamento, Emprestimo
import sys

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db':          db,
        'Equipamento': Equipamento,
        'Emprestimo':  Emprestimo
    }

if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else 'dev'

    if modo == 'prod':
        print("🚀 Servidor rodando em modo PRODUÇÃO")
        print("📡 Acesso da equipe: http://10.0.0.11:5000")
        app.run(debug=False, host='0.0.0.0', port=5000)
    else:
        print("🔧 Servidor rodando em modo DESENVOLVIMENTO")
        app.run(debug=True, host='0.0.0.0', port=5000)