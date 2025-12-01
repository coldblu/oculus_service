from pydantic import BaseModel
from typing import List, Optional

# Este é o modelo para CADA entidade/objeto que encontramos
class ExtractedEntity(BaseModel):
    value: str  # O texto exato (ex: "João Silva")
    label: str  # O tipo do objeto (ex: "PESSOA")

# Este é o modelo da Resposta JSON COMPLETA
class ExtractionResponse(BaseModel):
    file_name: Optional[str] = None  # Nome do arquivo (opcional)
    raw_text: str                   # texto bruto extraído
    extracted_entities: List[ExtractedEntity] # A lista de "objetos"