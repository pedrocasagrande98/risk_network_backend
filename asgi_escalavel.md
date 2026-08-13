# Guia de Evolução: Arquitetura Assíncrona e Escalável (ASGI + Workers)

Para transformar a API Risk Network em um sistema de alta performance, capaz de lidar com milhares de requisições simultâneas e processamentos pesados (como cálculos geoespaciais e relatórios) sem "travar", precisamos sair do modelo **WSGI Síncrono** e adotar o ecossistema **ASGI + Celery**.

Abaixo está o detalhamento técnico do que precisaria ser feito, por que deve ser feito e o nível de esforço envolvido.

---

## Fase 1: Mudança para ASGI (Requisições Assíncronas)
Atualmente o servidor roda via `Gunicorn + WSGI`. Quando 1 usuário faz uma requisição que demora 5 segundos para processar, o "worker" fica travado. Se tivermos apenas 2 workers, o terceiro usuário terá que esperar na fila.

O **ASGI** (Asynchronous Server Gateway Interface) permite que o Django libere o processador enquanto espera pelo banco de dados ou por uma API externa, atendendo centenas de outros usuários na mesma fração de tempo.

### O que precisaremos alterar?
1. **Instalar Servidor ASGI:** Substituir o Gunicorn puro pelo **Uvicorn** ou **Daphne**.
   - Comando: `poetry add uvicorn[standard]`
2. **Atualizar o Dockerfile/docker-compose:**
   - Trocar o comando de inicialização de:
     `gunicorn --bind 0.0.0.0:8000 core.wsgi:application`
   - Para:
     `uvicorn core.asgi:application --host 0.0.0.0 --port 8000 --workers 4`
3. **Refatorar Views (Opcional, mas recomendado):** O Django já suporta views assíncronas. Views que demoram (ex: que fazem chamadas a APIs externas ou bancos) devem ser transformadas em `async def` para aproveitarem a velocidade máxima.

---

## Fase 2: Background Jobs com Celery + Redis (Processamento em Segundo Plano)
Transformar a web em ASGI melhora o tráfego, mas e se o usuário pedir para gerar um relatório em PDF ou disparar 10.000 e-mails de alerta sobre um `GeoEvent` de Risco Crítico? O usuário não pode ficar 5 minutos olhando para um *loading* na tela.

Para isso, usamos **Filas de Tarefas (Message Brokers)**.

### O que precisaremos alterar?
1. **Adicionar o Redis no Docker:**
   O Redis será a memória rápida que guarda a "fila de coisas a fazer".
   - No `docker-compose.yml`, adicionar o serviço:
     ```yaml
     redis:
       image: redis:alpine
       ports:
         - "6379:6379"
     ```
2. **Instalar o Celery:**
   - Comando: `poetry add celery redis`
3. **Configurar o Celery no Django (`core/celery.py`):**
   - Criar o arquivo do Celery apontando para a URL do Redis (`redis://redis:6379/0`).
4. **Criar um novo Container para os "Trabalhadores" (Workers):**
   - No `docker-compose.yml`, duplicar o serviço `web`, renomear para `celery_worker`, e mudar o comando para:
     `celery -A core worker -l info`
5. **Escrever o Código Assíncrono (`tasks.py`):**
   - Tudo que for pesado (ex: notificar usuários sobre uma tempestade) será marcado com o decorador `@shared_task`. Na View, ao invés de executar a função na hora, chamamos `notificar_usuarios.delay()`. A View responde instantaneamente ao frontend e o Worker processa a notificação silenciosamente em segundo plano.

---

## Fase 3: Desacoplar para Escalabilidade Horizontal Infinita
Com ASGI e Celery, o código é imbatível. Mas, se a VPS atingir 100% de CPU, precisaremos de mais servidores. O problema atual é que o **Banco de Dados (Postgres)** está dentro do mesmo Docker da aplicação.

### O que precisaremos alterar?
1. **Banco de Dados Gerenciado (DBaaS):**
   - Contratar um banco de dados hospedado externamente (AWS RDS, Supabase, Neon, ou Hostinger Managed Postgres).
   - Atualizar a variável `DATABASE_URL` em todos os servidores para apontar para a nuvem.
   - *Por que?* Assim, você pode ter 10 VPS diferentes (ou usar serverless na AWS/GCP) rodando a sua API, e todas elas vão buscar dados na mesma fonte centralizada sem corromper a integridade.
2. **Balanceador de Carga (Load Balancer):**
   - Configurar o DNS (Cloudflare ou Hostinger) para dividir as requisições: 50% dos usuários vão para o Servidor A, 50% para o Servidor B.

---

## Resumo de Esforço
- **Fase 1 (ASGI):** Trabalho de 1 a 2 horas. Muito simples, poucas alterações no código.
- **Fase 2 (Celery/Redis):** Trabalho de 4 a 6 horas. Exige mexer na lógica da aplicação para separar o que é imediato do que é "background".
- **Fase 3 (DB Externo):** Trabalho DevOps (2 a 3 horas). Requer exportar e importar o banco de dados e mudar configurações de ambiente.

A sua aplicação hoje está sólida e perfeitamente aceitável para um MVP ou sistema de médio tráfego (já que o Cloudinary e o JWT tiram muito peso do servidor). Apenas implemente essa nova arquitetura quando o volume de acessos ou travamentos (timeouts) começarem a justificar o trabalho!
