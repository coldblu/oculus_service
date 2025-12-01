import base64
import logging
from .celery_config import celery_app
from .services.extraction import process_document

# Configura o logger
logger = logging.getLogger(__name__)


@celery_app.task(name="process_document_task")
def process_document_task(file_bytes_b64: str, mime_type: str, file_name: str):
    """
    Esta é a Tarefa Assíncrona que o Worker irá executar.

    Ela recebe os bytes do arquivo como uma string base64
    (pois é mais seguro para enviar via JSON para a fila).
    """
    try:
        logger.info(f"[CELERY_TASK] Recebida tarefa para: {file_name}")

        # 1. Decodifica os bytes de Base64
        file_bytes = base64.b64decode(file_bytes_b64)

        # 2. CHAMA EXATAMENTE A MESMA LÓGICA que o endpoint HTTP usa
        result_data = process_document(
            file_bytes=file_bytes,
            mime_type=mime_type,
            file_name=file_name
        )

        # 3. Processa o resultado
        # Por enquanto, vamos apenas logar.
        # No futuro, aqui é onde você chamaria sua API de Persistência:

        # --- INÍCIO DO CÓDIGO FUTURO ---
        # try:
        #     # Ex: Chamar a API de persistência em grafos
        #     response = requests.post(
        #         "http://api-de-persistencia:8080/v1/store-graph",
        #         json=result_data.model_dump() # Converte o Pydantic em dict
        #     )
        #     response.raise_for_status()
        #     logger.info(f"[CELERY_TASK] Resultado enviado para a API de Persistência para: {file_name}")
        # except Exception as e:
        #     logger.error(f"[CELERY_TASK] Falha ao enviar para API de Persistência: {e}")
        # --- FIM DO CÓDIGO FUTURO ---

        logger.info(f"[CELERY_TASK] Processamento concluído com sucesso para: {file_name}")

        # Retorna o nome do arquivo como prova de sucesso
        return f"Processado com sucesso: {file_name}"

    except Exception as e:
        logger.error(f"[CELERY_TASK] Falha catastrófica ao processar {file_name}: {e}", exc_info=True)
        # (O Celery pode ser configurado para tentar novamente em caso de falha)
        raise e