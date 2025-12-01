# Fase 1: A Base
# Usamos uma imagem oficial do Python 3.10 (baseada em Debian 12 'Bookworm')
# A versão 'slim' é menor e ideal para microsserviços.
FROM python:3.10-slim-bookworm

# Define o diretório de trabalho dentro do contêiner
WORKDIR /code

# Define variáveis de ambiente para o Python não criar cache
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Fase 2: Instalação das Dependências do Sistema (Linux)
# Aqui está a mágica: instalamos o Tesseract, o pacote de linguagem Português,
# e o Poppler (para ler PDFs) de uma só vez.
RUN apt-get update && \
    apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Fase 3: Instalação das Dependências do Python
# Primeiro, copiamos o arquivo de requisitos...
COPY requirements.txt requirements.txt

# ...e então instalamos tudo com o 'pip'
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
RUN python -m spacy download pt_core_news_lg

# Fase 4: Copiar o Código da Aplicação
# Copia o código da sua pasta 'app' local para dentro do contêiner
COPY ./app /code/app

# Fase 5: Comando de Execução
# Diz ao contêiner como iniciar nossa API (usando o servidor Uvicorn)
# Ele vai rodar o 'app' dentro do arquivo 'main' na pasta 'app'.
# O 'host 0.0.0.0' permite que ele seja acessado de fora do contêiner.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


