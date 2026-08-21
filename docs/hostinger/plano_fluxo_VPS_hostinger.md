# Plano de Deploy: Estrutura Modular VPS Hostinger

Este documento detalha o passo a passo para colocar a nova cadeia de Inteligência Artificial (Motor WTH e Motor OSMNX) em produção na sua VPS Hostinger, mantendo a arquitetura 100% modular e desacoplada do Risk Network Backend (que já está no ar).

---

## 1. Visão Geral da Arquitetura na VPS

Atualmente você tem o **Risk Network Backend** (Django + Celery + Redis) rodando na VPS, e o Frontend na **Vercel**. 

A nova arquitetura adicionará dois novos blocos independentes na sua VPS. Cada bloco rodará em seu próprio ecossistema de containers Docker:
- **Container A:** WTH FastAPI + WTH Celery
- **Container B:** OSMNX FastAPI + OSMNX Celery

Todos eles podem usar o mesmo servidor Redis que já está rodando na sua VPS para mensageria do Celery (basta apontar para bancos diferentes, ex: `redis://localhost:6379/1` e `/2`), ou você pode subí-los com seus próprios Redis independentes dentro do Docker.

---

## 2. Separação dos Repositórios GitHub

Para garantir a produção independente, você deverá criar **dois novos repositórios** no seu GitHub. 

### Repositório 1: `risk-network-wth-motor`
Este repositório será exclusivo para o cálculo de manchas d'água.
**Arquivos a subir:**
- `WTH_MOTOR_VALIDATE/main.py`
- `WTH_MOTOR_VALIDATE/worker.py`
- Arquivo `requirements.txt` (com as libs: `fastapi`, `uvicorn`, `celery`, `redis`, `rasterio`, `numpy`, `geojson`, `shapely`, `pyproj`).
- *Atenção:* Os arquivos `.tif` (que pesam mais de 2GB) **NÃO** devem subir para o GitHub. Eles devem ser transferidos diretamente para a VPS via SCP/SFTP (FileZilla) para uma pasta local, que será montada no Docker como um volume.

### Repositório 2: `risk-network-osmnx-motor`
Este repositório será exclusivo para o recorte de ruas e análise viária.
**Arquivos a subir:**
- `osmnx_street/main.py`
- `osmnx_street/worker.py`
- Arquivo `requirements.txt` (com as libs: `fastapi`, `uvicorn`, `celery`, `redis`, `osmnx`, `geopandas`, `shapely`).

---

## 3. Senhas e Variáveis de Ambiente (.env)

Antes de rodar na VPS, você precisará ter em mãos (ou definir no `.env` da VPS):

1. **Credenciais do Redis:** Se o seu Redis atual tem senha, você precisará da string de conexão: `redis://:SUA_SENHA@ip_do_redis:6379/1`.
2. **URLs Internas:** O `Risk Network Backend` (Django) precisará saber onde encontrar esses motores. No arquivo `georisk/processors.py` do Backend, você terá que trocar `127.0.0.1:8001` pelo IP ou DNS interno dos novos containers Docker.
   - Exemplo: `WTH_URL = "http://localhost:8001/api/v1/flood"`
   - Exemplo: `OSMNX_URL = "http://localhost:8002/api/v1/streets"`

---

## 4. Passo a Passo do Deploy (O que você fará)

### Fase 1: Preparação do Código (Local)
1. Crie os dois repositórios no GitHub e dê um `git push` do código de cada pasta separadamente.
2. Crie um arquivo `Dockerfile` e um `docker-compose.yml` para cada um dos repositórios. (O Dockerfile vai apenas instalar o Python e rodar o Uvicorn e o Celery).

### Fase 2: Configuração da VPS
1. Acesse sua VPS Hostinger via SSH.
2. Crie uma pasta raiz, ex: `/var/www/risk-ai-motors/`.
3. Faça o `git clone` dos dois repositórios.
4. **Transferência Pesada:** Use o FileZilla para enviar a pasta com os arquivos `.tif` do seu computador local direto para a VPS. Coloque na pasta do WTH Motor.

### Fase 3: Subindo os Containers
1. Entre na pasta do `wth-motor` na VPS e rode: `docker-compose up -d --build`.
   - Isso vai subir a API na porta `8001` e o Worker do Celery.
2. Entre na pasta do `osmnx-motor` e rode: `docker-compose up -d --build`.
   - Isso vai subir a API na porta `8002` e o Worker do Celery.
3. Teste dando um `curl http://localhost:8001/docs` de dentro da sua VPS para confirmar que estão rodando.

### Fase 4: Conectando com o Backend Django
1. Vá até o repositório do seu `Risk Network Backend`.
2. Atualize o arquivo `processors.py` enviando as portas configuradas (`8001` e `8002`) da VPS.
3. Reinicie o serviço do Django e o Celery Worker do Django na VPS.

---

## 5. Estimativa de Tempo

Como a lógica e os scripts já estão prontos e funcionando 100%, o esforço agora é puramente **DevOps**.

- **Criação de repositórios e organização do código:** ~1 hora.
- **Criação dos Dockerfiles e Docker-compose:** ~2 horas (ajustes de bibliotecas geográficas como GDAL no Linux costumam dar um pouco de trabalho no Docker).
- **Upload dos arquivos .tif para a VPS:** Depende da sua internet (são 2GB+, pode levar de 30 min a 2 horas via FTP).
- **Setup na VPS (Clone, Build Docker, Testes de porta):** ~2 horas.
- **Integração com o Backend Django atual:** ~30 minutos.

**Tempo Total Estimado:** Cerca de **6 a 8 horas de trabalho** (1 ou 2 dias focados apenas em infraestrutura).

## Dica Importante sobre a Hostinger
Modelos espaciais e a biblioteca `osmnx` consomem bastante Memória RAM. Certifique-se de que o seu plano VPS da Hostinger tem pelo menos **4GB de RAM** (Ideal 8GB) livres para suportar: Django, Redis, 3 Celery Workers simultâneos e o carregamento dos Raster .tif na memória. Se a memória estourar, os containers do Docker vão "morrer" silenciosamente por OOM (Out Of Memory).
