from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class OportunidadeModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    titulo: str
    link: str
    data_publicacao: Optional[str] = None
    data_limite: Optional[str] = None
    data_vencimento: Optional[str] = None
    status_vigencia: str = "vigente"
    status: Optional[str] = "vigente"
    categoria: str = "geral"
    fonte: str
    tags: List[str] = Field(default_factory=list)
    favorito: bool = False
    extra_info: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class EditalModel(OportunidadeModel):
    numero_edital: Optional[str] = None
    orgao_promotor: Optional[str] = None
    categoria: str = "edital"

class VagaEstagioModel(OportunidadeModel):
    empresa_contratante: Optional[str] = None
    bolsa: Optional[str] = None
    remuneracao: Optional[str] = None
    categoria: str = "estagio"

class NoticiaModel(OportunidadeModel):
    resumo: Optional[str] = None
    categoria: str = "noticia"

class EstatisticasPrazos(BaseModel):
    total: int = 0
    vigentes: int = 0
    vencendo_7dias: int = 0
    encerrados: int = 0
    sem_prazo: int = 0
    percentual_vigentes: float = 0.0
    categorias: Dict[str, int] = Field(default_factory=dict)

class UsuarioRegistroModel(BaseModel):
    nome: str
    email: str
    senha: str
    matricula: Optional[str] = None
    curso: Optional[str] = None
    consentimento_lgpd: bool = True

class UsuarioLoginModel(BaseModel):
    email: str
    senha: str

class UsuarioRespostaModel(BaseModel):
    id: str
    nome: str
    email: str
    matricula: Optional[str] = None
    curso: Optional[str] = None
    cursos_interesse: List[str] = Field(default_factory=list)
    areas_interesse: List[str] = Field(default_factory=list)
    favoritos: List[str] = Field(default_factory=list)
    receber_alertas: bool = False
    is_admin: bool = False
