from celery import Celery

# Define o endereço do nosso contêiner Redis
# 'redis://oculus_redis:6379/0'
# Usamos 'oculus_redis' pois é o nome do serviço no docker-compose.yml
REDIS_URL = "redis://redis_broker:6379/0"

# Cria a instância principal do Celery
celery_app = Celery(
    "oculus_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL, # Backend armazena os resultados (se precisarmos)
    include=["app.tasks"] # Lista de módulos onde o Celery deve procurar tarefas
)

# Configurações adicionais
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo", # Use o seu fuso horário
    enable_utc=True,
)

if __name__ == "__main__":
    celery_app.start()