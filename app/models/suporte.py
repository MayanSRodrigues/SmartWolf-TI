from app import db
from datetime import datetime

# Tabela associativa técnicos <-> chamado de suporte
chamado_suporte_tecnicos = db.Table('chamado_suporte_tecnicos',
    db.Column('chamado_id',  db.Integer, db.ForeignKey('chamados_suporte.id'), primary_key=True),
    db.Column('usuario_id',  db.Integer, db.ForeignKey('usuarios.id'),         primary_key=True)
)


class ChamadoSuporte(db.Model):
    __tablename__ = 'chamados_suporte'

    id            = db.Column(db.Integer, primary_key=True)
    titulo        = db.Column(db.String(200), nullable=False)
    descricao     = db.Column(db.Text, nullable=False)

    # Solicitante (pode ser externo — não precisa ter login)
    solicitante_nome  = db.Column(db.String(100), nullable=False)
    solicitante_email = db.Column(db.String(150), nullable=False)
    solicitante_setor = db.Column(db.String(100))

    # Classificação
    tipo        = db.Column(db.Enum('incidente', 'requisicao', 'problema', 'mudanca'),
                            nullable=False, default='requisicao')
    prioridade  = db.Column(db.Enum('baixa', 'media', 'alta', 'critica'),
                            nullable=False, default='media')
    status      = db.Column(db.Enum('aberto', 'em_andamento', 'pendente', 'resolvido', 'fechado'),
                            nullable=False, default='aberto')
    instituicao = db.Column(db.Enum('UniFECAF', 'ColégioSER'), nullable=True)

    # Técnico responsável principal + lista de técnicos
    tecnico_id  = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    tecnico     = db.relationship('Usuario', foreign_keys=[tecnico_id],
                                  backref='chamados_responsavel')
    tecnicos    = db.relationship('Usuario', secondary=chamado_suporte_tecnicos,
                                  backref='chamados_atribuidos')

    # Quem abriu no sistema
    aberto_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    aberto_por    = db.relationship('Usuario', foreign_keys=[aberto_por_id],
                                    backref='chamados_abertos')

    # Datas
    criado_em    = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em= db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolvido_em = db.Column(db.DateTime, nullable=True)
    fechado_em   = db.Column(db.DateTime, nullable=True)

    # Relacionamentos
    comentarios = db.relationship('ComentarioSuporte', backref='chamado',
                                  lazy=True, cascade='all, delete-orphan',
                                  order_by='ComentarioSuporte.criado_em')
    anexos      = db.relationship('AnexoSuporte', backref='chamado',
                                  lazy=True, cascade='all, delete-orphan')

    def tempo_aberto(self):
        fim   = self.resolvido_em or datetime.utcnow()
        delta = fim - self.criado_em
        horas = int(delta.total_seconds() // 3600)
        if horas < 24:
            return f'{horas}h'
        return f'{horas // 24}d {horas % 24}h'

    def to_dict(self, resumido=False):
        d = {
            'id':                self.id,
            'titulo':            self.titulo,
            'solicitante_nome':  self.solicitante_nome,
            'solicitante_email': self.solicitante_email,
            'solicitante_setor': self.solicitante_setor or '—',
            'tipo':              self.tipo,
            'prioridade':        self.prioridade,
            'status':            self.status,
            'instituicao':       self.instituicao or '—',
            'tecnico':           self.tecnico.nome if self.tecnico else '—',
            'tecnico_id':        self.tecnico_id,
            'tecnicos':          [{'id': t.id, 'nome': t.nome} for t in self.tecnicos],
            'aberto_por':        self.aberto_por.nome if self.aberto_por else '—',
            'tempo_aberto':      self.tempo_aberto(),
            'criado_em':         self.criado_em.strftime('%d/%m/%Y %H:%M'),
            'atualizado_em':     self.atualizado_em.strftime('%d/%m/%Y %H:%M'),
            'resolvido_em':      self.resolvido_em.strftime('%d/%m/%Y %H:%M') if self.resolvido_em else None,
            'total_comentarios': len(self.comentarios),
            'total_anexos':      len(self.anexos),
        }
        if not resumido:
            d['descricao']   = self.descricao
            d['comentarios'] = [c.to_dict() for c in self.comentarios]
            d['anexos']      = [a.to_dict() for a in self.anexos]
        return d


class ComentarioSuporte(db.Model):
    __tablename__ = 'comentarios_suporte'

    id         = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey('chamados_suporte.id'), nullable=False)
    autor_id   = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    autor      = db.relationship('Usuario', backref='comentarios_suporte')
    texto      = db.Column(db.Text, nullable=False)
    interno    = db.Column(db.Boolean, default=False)  # nota interna vs resposta ao cliente
    criado_em  = db.Column(db.DateTime, default=datetime.utcnow)

    anexos = db.relationship('AnexoSuporte', backref='comentario',
                             lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':        self.id,
            'autor':     self.autor.nome if self.autor else 'Sistema',
            'autor_id':  self.autor_id,
            'texto':     self.texto,
            'interno':   self.interno,
            'criado_em': self.criado_em.strftime('%d/%m/%Y %H:%M'),
            'anexos':    [a.to_dict() for a in self.anexos]
        }


class AnexoSuporte(db.Model):
    __tablename__ = 'anexos_suporte'

    id             = db.Column(db.Integer, primary_key=True)
    chamado_id     = db.Column(db.Integer, db.ForeignKey('chamados_suporte.id'), nullable=False)
    comentario_id  = db.Column(db.Integer, db.ForeignKey('comentarios_suporte.id'), nullable=True)
    nome_arquivo   = db.Column(db.String(255), nullable=False)
    tipo_mime      = db.Column(db.String(100))
    dados          = db.Column(db.LargeBinary)          # armazena o arquivo em binário
    tamanho        = db.Column(db.Integer)               # bytes
    criado_em      = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':           self.id,
            'nome_arquivo': self.nome_arquivo,
            'tipo_mime':    self.tipo_mime,
            'tamanho':      self.tamanho,
            'criado_em':    self.criado_em.strftime('%d/%m/%Y %H:%M'),
            'url':          f'/api/suporte/anexos/{self.id}'
        }
