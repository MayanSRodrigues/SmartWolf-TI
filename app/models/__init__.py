from app import db
from datetime import datetime, timedelta
from flask_login import UserMixin

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id            = db.Column(db.Integer, primary_key=True)
    nome          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(150), nullable=False, unique=True)
    senha_hash    = db.Column(db.String(255), nullable=False)
    nivel         = db.Column(db.Enum('admin', 'tecnico'), nullable=False, default='tecnico')
    ativo         = db.Column(db.Boolean, default=True)
    criado_em     = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acesso = db.Column(db.DateTime, nullable=True)

    chamados_registrados = db.relationship('Chamado', backref='registrado_por', lazy=True)

    def set_senha(self, senha):
        from werkzeug.security import generate_password_hash
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.senha_hash, senha)

    def is_admin(self):
        return self.nivel == 'admin'

    def to_dict(self):
        return {
            'id':            self.id,
            'nome':          self.nome,
            'email':         self.email,
            'nivel':         self.nivel,
            'ativo':         self.ativo,
            'criado_em':     self.criado_em.strftime('%d/%m/%Y %H:%M'),
            'ultimo_acesso': self.ultimo_acesso.strftime('%d/%m/%Y %H:%M') if self.ultimo_acesso else '—'
        }

class Categoria(db.Model):
    __tablename__ = 'categorias'

    id        = db.Column(db.Integer, primary_key=True)
    nome      = db.Column(db.String(100), nullable=False, unique=True)
    icone     = db.Column(db.String(10), default='📦')
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    equipamentos = db.relationship('Equipamento', backref='categoria', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'nome': self.nome, 'icone': self.icone}


class Equipamento(db.Model):
    __tablename__ = 'equipamentos'

    id                  = db.Column(db.Integer, primary_key=True)
    nome                = db.Column(db.String(100), nullable=False)
    patrimonio          = db.Column(db.String(50), unique=True, nullable=True)
    descricao           = db.Column(db.String(255))
    ativo               = db.Column(db.Boolean, default=True)
    categoria_id        = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=True)
    tipo                = db.Column(db.Enum('emprestavel','fixo','suprimento'), default='emprestavel')
    quantidade          = db.Column(db.Integer, default=1)
    quantidade_minima   = db.Column(db.Integer, default=1)
    localizacao         = db.Column(db.String(100))
    fornecedor          = db.Column(db.String(150))
    nota_fiscal         = db.Column(db.String(100))
    contrato_manutencao = db.Column(db.String(100))
    data_compra         = db.Column(db.Date, nullable=True)
    garantia_ate        = db.Column(db.Date, nullable=True)
    valor_compra        = db.Column(db.Numeric(10,2), nullable=True)
    criado_em           = db.Column(db.DateTime, default=datetime.utcnow)

    emprestimos   = db.relationship('Emprestimo',    backref='equipamento', lazy=True)
    movimentacoes = db.relationship('Movimentacao',  backref='equipamento', lazy=True)
    manutencoes   = db.relationship('Manutencao',    backref='equipamento', lazy=True)

    def garantia_status(self):
        if not self.garantia_ate:
            return 'sem_garantia'
        hoje = datetime.now().date()
        dias = (self.garantia_ate - hoje).days
        if dias < 0:
            return 'vencida'
        if dias <= 30:
            return 'vencendo'
        return 'valida'

    def estoque_baixo(self):
        return self.quantidade <= self.quantidade_minima

    def to_dict(self):
        return {
            'id':                  self.id,
            'nome':                self.nome,
            'patrimonio':          self.patrimonio or '—',
            'descricao':           self.descricao,
            'ativo':               self.ativo,
            'categoria_id':        self.categoria_id,
            'categoria':           self.categoria.nome if self.categoria else '—',
            'categoria_icone':     self.categoria.icone if self.categoria else '📦',
            'tipo':                self.tipo,
            'quantidade':          self.quantidade,
            'quantidade_minima':   self.quantidade_minima,
            'estoque_baixo':       self.estoque_baixo(),
            'localizacao':         self.localizacao or '—',
            'fornecedor':          self.fornecedor or '—',
            'nota_fiscal':         self.nota_fiscal or '—',
            'contrato_manutencao': self.contrato_manutencao or '—',
            'data_compra':         self.data_compra.strftime('%d/%m/%Y') if self.data_compra else None,
            'garantia_ate':        self.garantia_ate.strftime('%d/%m/%Y') if self.garantia_ate else None,
            'garantia_status':     self.garantia_status(),
            'valor_compra':        float(self.valor_compra) if self.valor_compra else None,
        }
    
class Chamado(db.Model):
    __tablename__ = 'chamados'

    id                           = db.Column(db.Integer, primary_key=True)
    responsavel                  = db.Column(db.String(100), nullable=False)
    email                        = db.Column(db.String(150), nullable=False)
    local_uso                    = db.Column(db.String(100), nullable=False)
    instituicao                  = db.Column(db.Enum('UniFECAF', 'ColégioSER'), nullable=False)
    turno                        = db.Column(db.Enum('manha', 'noite', 'outro'), nullable=False, default='outro')
    data_hora_entrega            = db.Column(db.DateTime, nullable=False)
    data_hora_devolucao_prevista = db.Column(db.DateTime, nullable=False)
    observacoes                  = db.Column(db.Text)
    status                       = db.Column(db.Enum('ativo', 'devolvido', 'em_atraso'), default='ativo', nullable=False)
    criado_em                    = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em                = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    registrado_por_id            = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    itens = db.relationship('Emprestimo', backref='chamado', lazy=True)

    def calcular_status(self):
        """Status do chamado baseado nos itens."""
        if not self.itens:
            return 'ativo'
        statuses = [e.calcular_status() for e in self.itens]
        if all(s == 'devolvido' for s in statuses):
            return 'devolvido'
        if any(s == 'em_atraso' for s in statuses):
            return 'em_atraso'
        return 'ativo'

    def to_dict(self):
        status_atual = self.calcular_status()
        return {
            'id':                           self.id,
            'responsavel':                  self.responsavel,
            'email':                        self.email,
            'local_uso':                    self.local_uso,
            'instituicao':                  self.instituicao,
            'turno':                        self.turno,
            'data_hora_entrega':            self.data_hora_entrega.strftime('%d/%m/%Y %H:%M'),
            'data_hora_devolucao_prevista': self.data_hora_devolucao_prevista.strftime('%d/%m/%Y %H:%M'),
            'observacoes':                  self.observacoes,
            'status':                       status_atual,
            'itens':                        [e.to_dict() for e in self.itens],
            'total_itens':                  len(self.itens),
            'itens_devolvidos':             sum(1 for e in self.itens if e.calcular_status() == 'devolvido'),
            'criado_em':                    self.criado_em.strftime('%d/%m/%Y %H:%M')
        }

class Emprestimo(db.Model):
    __tablename__ = 'emprestimos'

    id                           = db.Column(db.Integer, primary_key=True)
    equipamento_id               = db.Column(db.Integer, db.ForeignKey('equipamentos.id'), nullable=False)
    responsavel                  = db.Column(db.String(100), nullable=False)
    email                        = db.Column(db.String(150), nullable=False)
    local_uso                    = db.Column(db.String(100), nullable=False)
    instituicao                  = db.Column(db.Enum('UniFECAF', 'ColégioSER'), nullable=False)
    turno                        = db.Column(db.Enum('manha', 'noite', 'outro'), nullable=False, default='outro')
    data_hora_entrega            = db.Column(db.DateTime, nullable=False)
    data_hora_devolucao_prevista = db.Column(db.DateTime, nullable=False)
    data_hora_devolucao_real     = db.Column(db.DateTime, nullable=True)
    observacoes                  = db.Column(db.Text)
    status                       = db.Column(db.Enum('ativo', 'devolvido', 'em_atraso'), default='ativo', nullable=False)
    criado_em                    = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em                = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    chamado_id                   = db.Column(db.Integer, db.ForeignKey('chamados.id'), nullable=True)
    lembrete_enviado             = db.Column(db.Boolean, default=False)
    aviso_atraso_enviado         = db.Column(db.Boolean, default=False)

    def calcular_status(self):
        if self.data_hora_devolucao_real:
            return 'devolvido'
        agora  = datetime.now()
        limite = self.data_hora_devolucao_prevista + timedelta(hours=1)
        if agora > limite:
            return 'em_atraso'
        return 'ativo'

    def to_dict(self):
        return {
            'id':                           self.id,
            'equipamento_id':               self.equipamento_id,
            'equipamento':                  self.equipamento.nome if self.equipamento else '',
            'patrimonio':                   self.equipamento.patrimonio if self.equipamento else '',
            'responsavel':                  self.responsavel,
            'email':                        self.email,
            'local_uso':                    self.local_uso,
            'instituicao':                  self.instituicao,
            'turno':                        self.turno,
            'data_hora_entrega':            self.data_hora_entrega.strftime('%d/%m/%Y %H:%M'),
            'data_hora_devolucao_prevista': self.data_hora_devolucao_prevista.strftime('%d/%m/%Y %H:%M'),
            'data_hora_devolucao_real':     self.data_hora_devolucao_real.strftime('%d/%m/%Y %H:%M') if self.data_hora_devolucao_real else None,
            'observacoes':                  self.observacoes,
            'status':                       self.calcular_status(),
            'criado_em':                    self.criado_em.strftime('%d/%m/%Y %H:%M')
        }


class Movimentacao(db.Model):
    __tablename__ = 'movimentacoes'

    id             = db.Column(db.Integer, primary_key=True)
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamentos.id'), nullable=False)
    tipo           = db.Column(db.Enum('entrada','saida'), nullable=False)
    quantidade     = db.Column(db.Integer, nullable=False, default=1)
    motivo         = db.Column(db.String(255))
    responsavel    = db.Column(db.String(100))
    observacoes    = db.Column(db.Text)
    criado_em      = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':            self.id,
            'equipamento_id':self.equipamento_id,
            'equipamento':   self.equipamento.nome if self.equipamento else '',
            'patrimonio':    self.equipamento.patrimonio if self.equipamento else '',
            'tipo':          self.tipo,
            'quantidade':    self.quantidade,
            'motivo':        self.motivo,
            'responsavel':   self.responsavel,
            'observacoes':   self.observacoes,
            'criado_em':     self.criado_em.strftime('%d/%m/%Y %H:%M')
        }


class Manutencao(db.Model):
    __tablename__ = 'manutencoes'

    id             = db.Column(db.Integer, primary_key=True)
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamentos.id'), nullable=False)
    tipo           = db.Column(db.Enum('preventiva','corretiva','garantia'), nullable=False)
    descricao      = db.Column(db.Text, nullable=False)
    tecnico        = db.Column(db.String(100))
    empresa        = db.Column(db.String(150))
    custo          = db.Column(db.Numeric(10,2), nullable=True)
    data_entrada   = db.Column(db.DateTime, nullable=False)
    data_saida     = db.Column(db.DateTime, nullable=True)
    status         = db.Column(db.Enum('em_manutencao','concluida','cancelada'), default='em_manutencao')
    observacoes    = db.Column(db.Text)
    criado_em      = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':            self.id,
            'equipamento_id':self.equipamento_id,
            'equipamento':   self.equipamento.nome if self.equipamento else '',
            'patrimonio':    self.equipamento.patrimonio if self.equipamento else '',
            'tipo':          self.tipo,
            'descricao':     self.descricao,
            'tecnico':       self.tecnico or '—',
            'empresa':       self.empresa or '—',
            'custo':         float(self.custo) if self.custo else None,
            'data_entrada':  self.data_entrada.strftime('%d/%m/%Y %H:%M'),
            'data_saida':    self.data_saida.strftime('%d/%m/%Y %H:%M') if self.data_saida else None,
            'status':        self.status,
            'observacoes':   self.observacoes,
            'criado_em':     self.criado_em.strftime('%d/%m/%Y %H:%M')
        }