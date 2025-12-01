import pytesseract
import spacy
from pdf2image import convert_from_bytes
from PIL import Image
import io
import logging
import re  # Importa a biblioteca de Expressão Regular

from ..models.schemas import ExtractionResponse, ExtractedEntity

logger = logging.getLogger(__name__)

# --- Carregamento do Modelo de NLP (NER)
try:
    nlp = spacy.load("pt_core_news_lg")
    logger.info("Modelo spaCy 'pt_core_news_lg' carregado com sucesso.")
    logger.info("Adicionando regras customizadas de 'O_QUE' (EntityRuler)...")
    # Lista de termos que definem "O QUE" em acervos
    # Adicionamos variações (singular, plural).
    # O padrão [{"lower": "termo"}] garante que pegamos maiúsculas ou minúsculas.
    o_que_patterns = [
        {"label": "O_QUE", "pattern": [{"lower": "carta"}]},
        {"label": "O_QUE", "pattern": [{"lower": "cartas"}]},
        {"label": "O_QUE", "pattern": [{"lower": "documento"}]},
        {"label": "O_QUE", "pattern": [{"lower": "documentos"}]},
        {"label": "O_QUE", "pattern": [{"lower": "relatório"}]},
        {"label": "O_QUE", "pattern": [{"lower": "relatórios"}]},
        {"label": "O_QUE", "pattern": [{"lower": "fotografia"}]},
        {"label": "O_QUE", "pattern": [{"lower": "fotografias"}]},
        {"label": "O_QUE", "pattern": [{"lower": "ato"}]},
        {"label": "O_QUE", "pattern": [{"lower": "atos"}]},
        {"label": "O_QUE", "pattern": [{"lower": "decreto"}]},
        {"label": "O_QUE", "pattern": [{"lower": "decretos"}]},
        {"label": "O_QUE", "pattern": [{"lower": "ofício"}]},
        {"label": "O_QUE", "pattern": [{"lower": "ofícios"}]},
        {"label": "O_QUE", "pattern": [{"lower": "manuscrito"}]},
        {"label": "O_QUE", "pattern": [{"lower": "manuscritos"}]},
    ]

    # Adiciona o EntityRuler à pipeline do spaCy
    # 'before="ner"' é crucial. Nossas regras rodam ANTES do modelo de ML.
    # O modelo de ML (ner) vai então respeitar as entidades que já encontramos.
    ruler = nlp.add_pipe("entity_ruler", before="ner", config={"validate": True})
    ruler.add_patterns(o_que_patterns)

    logger.info(f"EntityRuler adicionado com {len(o_que_patterns)} padrões.")

except IOError:
    logger.error(
        "Erro fatal: Modelo 'pt_core_news_lg' não encontrado. Certifique-se de baixá-lo (python -m spacy download pt_core_news_lg)")
    nlp = None


def process_document(file_bytes: bytes, mime_type: str, file_name: str = None) -> ExtractionResponse:
    """
    Função principal do serviço. Recebe os bytes do arquivo e seu tipo,
    e orquestra a pipeline de OCR e NER.
    """
    logger.info(f"Iniciando processamento para o tipo: {mime_type}")

    raw_text = ""

    try:
        if mime_type == "application/pdf":
            logger.info("Tipo PDF detectado. Iniciando extração de PDF...")
            raw_text = _extract_text_from_pdf(file_bytes)
        elif mime_type in ["image/png", "image/jpeg", "image/tiff"]:
            logger.info("Tipo Imagem detectado. Iniciando extração de Imagem...")
            raw_text = _extract_text_from_image(file_bytes)
        else:
            raise ValueError(f"Tipo de arquivo não suportado: {mime_type}")

        logger.info(f"Extração de OCR concluída. Total de caracteres: {len(raw_text)}")
        if not raw_text.strip():
            logger.warning(
                "OCR não retornou texto. O documento pode estar em branco ou ser uma imagem pura (sem texto).")
            return ExtractionResponse(raw_text="", extracted_entities=[])

    except Exception as ocr_error:
        logger.error(f"Erro durante a fase de OCR: {ocr_error}", exc_info=True)
        raise ocr_error

    if nlp is None:
        logger.error("Modelo NLP não carregado. Pulando a extração de entidades.")
        raise RuntimeError("Modelo NLP (spaCy) não está disponível.")

    logger.info("Texto bruto extraído. Iniciando extração de entidades (NER)...")
    entities = _extract_entities_from_text(raw_text)
    logger.info(f"Extração de NER concluída. Entidades encontradas: {len(entities)}")

    response = ExtractionResponse(
        raw_text=raw_text,
        extracted_entities=entities,
        file_name=file_name,
    )

    return response


def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Recebe os bytes de um PDF, usa pdf2image para converter páginas em
    imagens, e passa cada imagem para o Tesseract.
    """
    try:
        images = convert_from_bytes(pdf_bytes, poppler_path=None, fmt='jpeg')
    except Exception as e:
        logger.error(f"Falha ao converter PDF para imagens (pdf2image/poppler): {e}")
        raise RuntimeError(f"Falha ao processar PDF com Poppler: {e}")

    full_text = ""

    for i, page_image in enumerate(images):
        logger.info(f"Processando PDF - Página {i + 1}/{len(images)}")
        try:
            page_text = pytesseract.image_to_string(page_image, lang='por')
            full_text += page_text + "\n\n--- Fim da Página --- \n\n"
        except Exception as tesseract_error:
            logger.error(f"Erro do Tesseract na página {i + 1}: {tesseract_error}")
            full_text += f"\n\n--- Erro ao ler a Página {i + 1} ---\n\n"

    return full_text


def _extract_text_from_image(image_bytes: bytes) -> str:
    """
    Recebe os bytes de uma imagem e passa para o Tesseract.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang='por')
        return text
    except Exception as e:
        logger.error(f"Falha ao processar imagem (Pillow/Tesseract): {e}")
        raise RuntimeError(f"Falha ao ler imagem: {e}")


def _map_spacy_label_to_catalog(spacy_label: str) -> str:
    """
    Converte as etiquetas padrão do spaCy para as "Máximas" da catalogação.
    """
    # Nossas regras do EntityRuler já usam "O_QUE", então checamos primeiro.
    if spacy_label == "O_QUE":
        return "O_QUE"

    if spacy_label == "PER":
        return "QUEM"  # Pessoa
    if spacy_label == "ORG":
        return "QUEM"  # Organização
    if spacy_label == "LOC":
        return "ONDE"  # Local
    if spacy_label == "GPE":
        return "ONDE"  # Entidade Geo-Política

    # Usamos MISC (Miscelânea) como um "pega-tudo" para "O_QUE"
    if spacy_label == "MISC":
        return "O_QUE"

    return spacy_label


def _extract_entities_from_text(text: str) -> list[ExtractedEntity]:
    """
    Recebe o texto bruto e usa o spaCy (NER) para encontrar os "objetos"
    e mapeá-los para as "Máximas da Catalogação".
    """
    doc = nlp(text)

    entities = []

    # Itera sobre as "entidades" (objetos) que o spaCy encontrou
    # (Isso agora inclui nossas regras E o modelo de ML)
    for ent in doc.ents:
        catalog_label = _map_spacy_label_to_catalog(ent.label_)

        # Vamos adicionar apenas as entidades que *queremos*
        if catalog_label in ["QUEM", "ONDE", "O_QUE"]:
            clean_value = re.sub(r'\s+', ' ', ent.text).strip()
            if clean_value:
                entities.append(
                    ExtractedEntity(
                        value=clean_value,
                        label=catalog_label
                    )
                )

    # Lidar com "QUANDO" (Datas)
    # Regra simples para datas no formato DD/MM/AAAA ou anos isolados
    date_pattern = re.compile(r'\b(\d{1,2}[/\.-]\d{1,2}[/\.-]\d{2,4})\b|\b(entre \d{4} e \d{4})\b|\b(\d{4})\b')

    for match in date_pattern.finditer(text):
        date_str = match.group(1) or match.group(2) or match.group(3)
        date_str = date_str.strip()
        clean_date_str = re.sub(r'\s+', ' ', date_str).strip()
        # Evitar capturar números de 4 dígitos que não sejam anos
        if len(clean_date_str) == 4:
            try:
                year = int(clean_date_str)
                if not (1000 <= year <= 2099):
                    continue
            except ValueError:
                continue

        # Só adiciona se a data limpa não for uma string vazia
        if clean_date_str:
            entities.append(
                ExtractedEntity(
                    value=clean_date_str,
                    label="QUANDO"
                )
            )

    # Remover duplicatas que podem ter sido pegas tanto pelo NER quanto pelo Regex
    unique_entities = []
    seen = set()
    for entity in entities:
        # Normaliza o valor para minúsculas para verificar duplicatas
        key = (entity.value.lower(), entity.label)
        if key not in seen:
            seen.add(key)
            unique_entities.append(entity)

    return unique_entities