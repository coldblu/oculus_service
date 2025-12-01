from fastapi import FastAPI, UploadFile, File, HTTPException, status
from .models.schemas import ExtractionResponse
from .services import extraction
import logging

# Configuração básica de log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cria a aplicação FastAPI
app = FastAPI(
    title="Oculus Service",
    description="Um microsserviço que extrai texto e entidades de documentos (PDFs e Imagens).",
    version="0.1.0"
)


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Monitoramento"])
async def health_check():
    """
    Endpoint de "Verificação de Saúde" (Health Check).
    Usado para saber se a API está no ar e respondendo.
    """
    return {"status": "ok", "service": "Oculus"}


@app.post("/v1/extract",
          response_model=ExtractionResponse,
          tags=["Extração"])
async def extract_data_from_document(
        file: UploadFile = File(...)
):
    """
    Endpoint principal. Recebe um documento (PDF ou Imagem), 
    extrai o texto (OCR) e as entidades (NER).
    """
    logger.info(f"Recebido arquivo: {file.filename} (Tipo: {file.content_type})")

    # Verifica se o tipo de arquivo é suportado
    if file.content_type not in ["application/pdf", "image/png", "image/jpeg", "image/tiff"]:
        logger.warning(f"Tipo de arquivo não suportado: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo de arquivo '{file.content_type}' não suportado. Use PDF, PNG, JPEG ou TIFF."
        )

    try:
        # Lê o conteúdo do arquivo em bytes
        contents = await file.read()

        # Chama nosso serviço "cérebro" para fazer o trabalho pesado
        # (Por enquanto, este serviço ainda é um esqueleto)
        result = extraction.process_document(
            file_bytes=contents,
            mime_type=file.content_type,
            file_name = file.filename
        )

        logger.info(f"Extração concluída para: {file.filename}")
        return result

    except Exception as e:
        logger.error(f"Erro ao processar o arquivo {file.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro interno ao processar o arquivo: {str(e)}"
        )