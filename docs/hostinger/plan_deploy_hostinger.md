# Plano de Migração do Backend (Render -> Hostinger VPS)

## 1. Análise da Aplicação Atual (risk_network_backend)
A aplicação é construída em **Django 6** com **Django Rest Framework**, gerenciada pelo **Poetry**, e conectada a um banco de dados **PostgreSQL** (atualmente provisionado no Render via `render.yaml`). Também possui integração com **Cloudinary** para armazenamento de mídia.

## 2. Esforço e Viabilidade
- **Viabilidade**: 100% Viável.
- **Esforço Estimado**: Baixo a Médio (1 a 2 horas).
- **Trabalho Necessário**: A aplicação não possui arquivos Docker. Teremos que "Dockerizar" o projeto para rodá-lo ao lado da nossa outra API (`hydro_osmnx_api`) na mesma VPS Hostinger, utilizando portas diferentes.

## 3. Passo a Passo da Migração

### Passo 1: Criação da Infraestrutura Docker (Localmente)
Teremos que criar dois arquivos na raiz deste repositório:
1. **`Dockerfile`**: Vai preparar um ambiente Python limpo, instalar o Poetry, rodar `poetry install` e liberar a aplicação via `gunicorn`.
2. **`docker-compose.yml`**: Vai orquestrar dois serviços:
   - Serviço `web` (Django na porta `8002:8000`).
   - Serviço `db` (PostgreSQL local na VPS com banco `risk_network_db`).

### Passo 2: Variáveis de Ambiente (.env na VPS)
Na VPS, precisaremos configurar um arquivo `.env` com as chaves vitais para a aplicação funcionar (substituindo as variáveis injetadas automaticamente pelo Render):
```env
DEBUG=False
SECRET_KEY=sua_chave_secreta_aqui
DATABASE_URL=postgres://risk_user:risk_password@db:5432/risk_network_db
CLOUDINARY_URL=sua_url_do_cloudinary
```

### Passo 3: Deploy na Hostinger
No terminal SSH da Hostinger, executaremos:
1. `git clone` deste repositório na pasta `/root/risk_network_backend`.
2. `docker compose up -d --build`.
3. Migrar o banco de dados e criar o super usuário:
   - `docker exec -it risk_network-web-1 poetry run python manage.py migrate`
   - `docker exec -it risk_network-web-1 poetry run python manage.py createsuperuser`

### Passo 4: Configurar Nginx (Opcional/Recomendado)
Para não ter que acessar a API pela porta `8002` bruta (ex: `http://187.77.61.11:8002`), podemos adicionar um bloco no `nginx.conf` da VPS que já configuramos hoje, fazendo um proxy. Por exemplo, tudo que for para `/api/risk/` vai para esta nova aplicação, e tudo que for para `/api/hydro/` vai para a aplicação antiga. Ou podemos simplesmente usar a porta `8002`.

### Passo 5: Ajuste no Frontend (Vercel)
No painel da Vercel (onde o front-end está hospedado):
1. Alterar a variável de ambiente (geralmente `VITE_API_URL` ou `REACT_APP_API_URL`).
2. Trocar de `https://risk-network-api.onrender.com` (ou similar) para `http://187.77.61.11:8002`.
3. Fazer o *Redeploy* do Frontend na Vercel.

---

*Documento gerado como base para a próxima iteração. Quando estiver pronto para continuar em outro workspace, basta seguir estes passos de Dockerização e subir para a VPS!*
