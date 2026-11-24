"""
Modelos de dados (Pydantic) para validação e serialização de requisições e respostas.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class ItemSchema(BaseModel):
    id: str
    nome: str
    descricao: Optional[str] = ""
    imagem_url: Optional[str] = ""
    categoria: Optional[str] = "brinde"
    curso_alvo: Optional[str] = "todos"
    rating_elo: float = 1000.0
    jogos: int = 0
    vitorias: int = 0
    derrotas: int = 0
    taxa_vitoria: float = 0.0
    forca_bt: float = 1.0
    prob_vitoria_media: float = 50.0
    ativo: int = 1


class ItemCreate(BaseModel):
    id: Optional[str] = None
    nome: str = Field(..., min_length=1)
    descricao: Optional[str] = ""
    imagem_url: Optional[str] = ""
    categoria: Optional[str] = "brinde"
    curso_alvo: Optional[str] = "todos"


class ItemUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    imagem_url: Optional[str] = None
    ativo: Optional[int] = None
    categoria: Optional[str] = None
    curso_alvo: Optional[str] = None


class ProximoParResponse(BaseModel):
    status: str = "ok"
    mensagem: Optional[str] = None
    categoria: Optional[str] = "brinde"
    itemA: Optional[dict] = None
    itemB: Optional[dict] = None
    totalRespondidosUsuario: int = 0
    totalItensAtivos: int = 0


class VotoRequest(BaseModel):
    uid: str = Field(..., min_length=1)
    canal: Optional[str] = "geral"
    categoria: Optional[str] = "brinde"
    item_a_id: str = Field(..., min_length=1)
    item_b_id: str = Field(..., min_length=1)
    vencedor_id: str = Field(..., min_length=1)


class VotoResponse(BaseModel):
    status: str = "ok"
    mensagem: str
    delta_elo: float
    novo_elo_vencedor: float
    novo_elo_perdedor: float
    total_usuario: int


class InscricaoFormRequest(BaseModel):
    uid: str = Field(..., min_length=1)
    iniciativa: Optional[str] = "Geral"
    nome: str = Field(..., min_length=2)
    email: str = Field(..., min_length=5)
    telefone: str = Field(..., min_length=8)
    universidade: Optional[str] = "UFMG - Universidade Federal de Minas Gerais"
    curso: str = Field(..., min_length=2)
    ano_graduacao: Optional[str] = ""
    vagas_6meses: Optional[str] = ""
    fatores_estagio: List[str] = Field(default_factory=list)
    como_conheceu: Optional[str] = ""
    # Novos campos fiéis ao formulário oficial da Mercado em Conexão (UFMG)
    como_soube_opcao: Optional[str] = ""
    projeto_extensao: Optional[str] = ""
    empresas_desejadas: Optional[str] = ""
    temas_painel: List[str] = Field(default_factory=list)
    tema_outro: Optional[str] = ""
    periodo_palestras: Optional[str] = ""
    horario_feira: Optional[str] = ""


class EstatisticasTorneio(BaseModel):
    total_itens: int
    itens_brindes: int
    itens_palestras: int
    total_duelos: int
    duelos_brindes: int
    duelos_palestras: int
    total_participantes: int
    total_inscritos: int
    brinde_lider: Optional[str] = None
    brinde_lider_elo: Optional[float] = None
    palestra_lider: Optional[str] = None
    palestra_lider_elo: Optional[float] = None
