from app import create_app, db
from app.models import Equipamento, Emprestimo, Chamado, Usuario
import sys
import os

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db':          db,
        'Equipamento': Equipamento,
        'Emprestimo':  Emprestimo,
        'Chamado':     Chamado,
        'Usuario':     Usuario
    }

if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else 'dev'
    if modo == 'prod':
        print("🚀 SmartWolf TI — Modo PRODUÇÃO")
        app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    else:
        print("🔧 SmartWolf TI — Modo DESENVOLVIMENTO")
        app.run(debug=True, host='0.0.0.0', port=5000)