# Microsserviço Oculus (OCR/NER)

![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Tesseract](https://img.shields.io/badge/Tesseract-000000?style=for-the-badge&logo=tesseract&logoColor=white)

Um microsserviço de **OCR (Optical Character Recognition)** e **NER (Named Entity Recognition)** robusto, "contêinerizado" e pronto para produção.

O **Oculus** é projetado para receber documentos (PDFs e imagens) e extrair não apenas o texto bruto, mas também entidades de catalogação específicas, prontas para serem consumidas por APIs de grafos (RDF) ou outros sistemas de acervo.

## 🎯 Objetivo

Este serviço foi criado para servir como um componente de IA especializado dentro de uma arquitetura de microsserviços. Ele resolve dois problemas centrais:

1.  **OCR (Tesseract):** Converte imagens e páginas de PDF em texto simples.
2.  **NER (spaCy):** Analisa esse texto e extrai "objetos" de catalogação baseados nas "Máximas da Catalogação":
    * **QUEM** (Pessoas e Organizações)
    * **QUANDO** (Datas e Anos)
    * **ONDE** (Locais e Endereços)
    * **O QUE** (Termos de catálogo customizados, ex: "Carta", "Relatório", "Manuscrito")

## ✨ Funcionalidades

* **Endpoint único** `POST /v1/extract` para processamento de documentos.
* **Suporte a múltiplos formatos:** Aceita `application/pdf`, `image/png`, `image/jpeg` e `image/tiff`.
* **Processamento de PDF multi-página:** Converte automaticamente PDFs de múltiplas páginas em texto contínuo.
* **Stack Robusta:**
    * **Docker:** 100% contêinerizado. A única dependência é o Docker Desktop.
    * **Python 3.10** como linguagem base.
    * **FastAPI** para uma API de alta performance e assíncrona.
    * **Tesseract:** O motor de OCR open-source mais poderoso.
    * **Poppler:** Para renderização de PDFs.
    * **spaCy:** Para reconhecimento de entidades (NER) de nível industrial, usando o modelo `pt_core_news_lg`.
* **Extensível:** Facilmente customizável para reconhecer novos termos de catálogo (ver [Customização](#customização)).

## 🚀 Como Rodar o Projeto

Este projeto é 100% gerenciado pelo Docker e Docker Compose.

### Pré-requisitos

1.  **Docker Desktop** (ou Docker Engine no Linux).
2.  **Git** (para clonar o repositório).

### Passos para Execução

1.  Clone este repositório:
    ```bash
    git clone [https://github.com/seu-usuario/oculus_service.git](https://github.com/seu-usuario/oculus_service.git)
    cd oculus_service
    ```

2.  Suba o serviço com o Docker Compose:
    ```bash
    docker compose up --build
    ```
    *Na primeira vez, este comando irá demorar alguns minutos*, pois ele precisa baixar a imagem do Python, instalar o Tesseract, o Poppler e o modelo de linguagem do spaCy (que tem +500MB).

3.  É isso! O servidor estará rodando e ouvindo na porta `8000`.

Você verá um log confirmando que o servidor está no ar:

````

oculus\_api  | INFO:     Uvicorn running on [http://0.0.0.0:8000](http://0.0.0.0:8000) (Press CTRL-C to quit)

````

## 🕹️ Como Usar

### 1. Documentação Interativa (Swagger)

A forma mais fácil de testar é pela documentação interativa que o FastAPI cria automaticamente.

Abra seu navegador e acesse:
[**http://localhost:8000/docs**](http://localhost:8000/docs)

Você pode clicar no endpoint `/v1/extract`, "Try it out" e enviar um arquivo PDF ou imagem diretamente pelo navegador.

### 2. Chamada via cURL

Você pode usar o `curl` (ou qualquer cliente de API como Postman/Insomnia) para enviar seu documento.

```bash
curl -X 'POST' \
  'http://localhost:8000/v1/extract' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@/caminho/completo/para/seu/documento.pdf;type=application/pdf'
````

*(Substitua `/caminho/completo/para/seu/documento.pdf` pelo caminho real do seu arquivo)*

-----

## 🏛️ Design da API

### Endpoint: `POST /v1/extract`

Recebe um único arquivo e retorna as entidades extraídas.

**Request Body:** `multipart/form-data`

  * **key:** `file`
  * **value:** O arquivo (ex: `meu_documento.pdf`)

**Success Response (200 OK):**

O serviço retorna um JSON com a seguinte estrutura:

```json
{
  "file_name": "Santos Dumont.pdf",
  "raw_text": "Texto completo extraído do PDF... (longa string)\n\n--- Fim da Página --- \n\n...",
  "extracted_entities": [
    {
      "value": "Alberto Santos Dumont",
      "label": "QUEM"
    },
    {
      "value": "Palmira",
      "label": "ONDE"
    },
    {
      "value": "Guarujá",
      "label": "ONDE"
    },
    {
      "value": "1873",
      "label": "QUANDO"
    },
    {
      "value": "1932",
      "label": "QUANDO"
    },
    {
      "value": "Torre Eiffel",
      "label": "ONDE"
    },
    {
      "value": "Prêmio Deutsch",
      "label": "O_QUE"
    },
    {
      "value": "1901",
      "label": "QUANDO"
    },
    {
      "value": "Paris",
      "label": "ONDE"
    },
    {
      "value": "carta",
      "label": "O_QUE"
    },
    {
      "value": "documento",
      "label": "O_QUE"
    }
  ]
}
```

## 🔧 Customização (Adicionando mais "Objetos")

Para adicionar novos termos de catálogo (ex: "mapa", "diário", "ata"), você não precisa de um novo modelo de IA. Basta adicionar as palavras à lista de regras do spaCy (`EntityRuler`).

1.  Abra o arquivo: `app/services/extraction.py`
2.  Localize a lista `o_que_patterns` (próximo ao topo do arquivo).
3.  Adicione seus novos padrões. O formato `{"lower": "palavra"}` garante que ele pegue "mapa", "Mapa" ou "MAPA".

<!-- end list -->

```python
# app/services/extraction.py

o_que_patterns = [
    {"label": "O_QUE", "pattern": [{"lower": "carta"}]},
    {"label": "O_QUE", "pattern": [{"lower": "cartas"}]},
    {"label": "O_QUE", "pattern": [{"lower": "documento"}]},
    {"label": "O_QUE", "pattern": [{"lower": "documentos"}]},
    {"label": "O_QUE", "pattern": [{"lower": "relatório"}]},
    
    # Adicione suas novas regras aqui
    {"label": "O_QUE", "pattern": [{"lower": "mapa"}]},
    {"label": "O_QUE", "pattern": [{"lower": "mapas"}]},
    {"label":S: "O_QUE", "pattern": [{"lower": "diário"}]},
]
```

4.  Pare o servidor (`Ctrl+C` no terminal) e rode-o novamente (`docker compose up`). As novas regras serão carregadas automaticamente.