from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Cadastro(db.Model):
    __tablename__ = 'cadastros'
    
    id = db.Column(db.Integer, primary_key=True)
    protocolo = db.Column(db.String(50), unique=True, nullable=False)
    
    # Dados Pessoais
    nome_completo = db.Column(db.String(200), nullable=False)
    cpf = db.Column(db.String(14), nullable=False)
    rg = db.Column(db.String(20), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    
    # Endereço
    endereco_rua = db.Column(db.String(200), nullable=False)
    endereco_numero = db.Column(db.String(10), nullable=False)
    endereco_bairro = db.Column(db.String(100), nullable=False)
    endereco_cidade = db.Column(db.String(100), nullable=False, default='Angatuba')
    endereco_estado = db.Column(db.String(2), nullable=False, default='SP')
    endereco_cep = db.Column(db.String(9), nullable=False)
    
    # Contato e Residência
    telefone = db.Column(db.String(15), nullable=False)
    tempo_fixacao = db.Column(db.Integer, nullable=False)
    
    # Informações Familiares
    quantidade_pessoas = db.Column(db.Integer, nullable=False)
    moradores = db.Column(db.Text)
    renda_familiar = db.Column(db.Float, nullable=False)
    
    # Situação Habitacional e Social
    possui_imovel = db.Column(db.String(3), nullable=False)  # 'sim' ou 'nao'
    programa_social = db.Column(db.String(3), nullable=False)  # 'sim' ou 'nao'
    
    # Auto Declaração
    auto_declaracao_pcd = db.Column(db.Boolean, default=False)
    auto_declaracao_idoso = db.Column(db.Boolean, default=False)
    auto_declaracao_outros = db.Column(db.Boolean, default=False)
    auto_declaracao_outros_descricao = db.Column(db.Text)
    
    # Documentos Anexados
    documentos = db.Column(db.Text) # Armazenará um JSON de nomes de arquivos
    
    # Metadados
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Cadastro {self.protocolo}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'protocolo': self.protocolo,
            'nome_completo': self.nome_completo,
            'cpf': self.cpf,
            'rg': self.rg,
            'data_nascimento': self.data_nascimento.isoformat() if self.data_nascimento else None,
            'endereco': {
                'rua': self.endereco_rua,
                'numero': self.endereco_numero,
                'bairro': self.endereco_bairro,
                'cidade': self.endereco_cidade,
                'estado': self.endereco_estado,
                'cep': self.endereco_cep
            },
            'telefone': self.telefone,
            'tempo_fixacao': self.tempo_fixacao,
            'quantidade_pessoas': self.quantidade_pessoas,
            'moradores': self.moradores,
            'renda_familiar': self.renda_familiar,
            'possui_imovel': self.possui_imovel,
            'programa_social': self.programa_social,
            'auto_declaracao': {
                'pcd': self.auto_declaracao_pcd,
                'idoso': self.auto_declaracao_idoso,
                'outros': self.auto_declaracao_outros,
                'outros_descricao': self.auto_declaracao_outros_descricao
            },
            'documentos': json.loads(self.documentos) if self.documentos else [],
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None
        }

