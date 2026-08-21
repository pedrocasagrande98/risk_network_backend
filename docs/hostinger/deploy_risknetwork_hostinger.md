# Guia de Deploy Definitivo: Risk Network (VPS Hostinger + Vercel)

Este guia documenta todos os passos, erros encontrados e soluções aplicadas durante o deploy da API **Risk Network Backend** em uma VPS da Hostinger, com o Front-end hospedado na Vercel.

---

## 1. Preparação da Aplicação (Dockerização)
Para evitar conflitos com outras APIs e facilitar a implantação, a aplicação foi colocada em containers Docker.

**Arquivos Criados na Raiz do Projeto:**
- `Dockerfile`: Usa a imagem `python:3.13-slim`, instala dependências do sistema (PostgreSQL client) e instala pacotes Python via **Poetry**.
- `docker-compose.yml`: Sobe os serviços `web` (Django via Gunicorn na porta `8002`) e `db` (PostgreSQL 15).
- `.dockerignore`: Para evitar enviar a pasta local `venv/` e arquivos de sistema para dentro do container.
- `.env.example`: Modelo padrão de variáveis.

*(Após a criação desses arquivos, fizemos um `git push` para o repositório principal).*

---

## 2. Acesso e Clonagem na VPS
1. Acesse a VPS via SSH.
2. Clone o repositório usando o Personal Access Token (PAT) do GitHub, pois senhas normais não funcionam mais:
   ```bash
   git clone https://github.com/SEU_USUARIO/risk_network_backend.git
   ```
3. Crie o arquivo `.env` na VPS e rode o Docker:
   ```bash
   docker compose up -d --build
   ```
4. Aplique as migrações e crie o Superusuário:
   ```bash
   docker exec -it risk_network_backend-web-1 poetry run python manage.py migrate
   docker exec -it risk_network_backend-web-1 poetry run python manage.py createsuperuser
   ```

---

## 3. Configuração de DNS (Apontamento do Domínio)
Para resolver o problema de **Mixed Content** (onde a Vercel HTTPS recusa conversar com o backend HTTP), precisávamos adicionar SSL na API.

1. Descubra o verdadeiro IP IPv4 da sua VPS:
   ```bash
   curl -4 ifconfig.me
   ```
2. No painel da Hostinger -> Domínios -> DNS / Nameservers, crie ou edite um registro do tipo **A**:
   - **Nome:** `api`
   - **Aponta para:** `<COLE O IPv4 DA VPS AQUI>`
   *(Cuidado: IPs como `2.57.91.91` são páginas de estacionamento da Hostinger e farão o Certbot falhar).*

---

## 4. Liberação da Porta 80 na VPS
O Nginx e o Certbot precisam da porta `80` para funcionarem.

**Problema Encontrado:** Outra API (`hydro_osmnx_api`) possuía um container Nginx mapeando as portas `80:80`. 
**Solução:** 
1. Comentamos o serviço `nginx` no `docker-compose.yml` da API antiga.
2. Atualizamos na VPS e removemos o container fantasma:
   ```bash
   cd /root/hydro_osmnx_api
   docker compose up -d --remove-orphans
   ```
*(Se estiver em dúvida sobre quem está usando a porta 80, use `lsof -i :80` ou `netstat -tulnp | grep :80`).*

---

## 5. Configuração do Nginx Nativo (Host)
1. Instale o Nginx e Certbot:
   ```bash
   apt-get update && apt-get install -y nginx certbot python3-certbot-nginx
   ```
2. Crie o arquivo de configuração:
   ```bash
   nano /etc/nginx/sites-available/risk_network
   ```
3. **Configuração à Prova de Erros 500 (Crucial para o Certbot):**
   ```nginx
   server {
       listen 80;
       server_name api.SEUDOMINIO.com;

       # Garante que o Let's Encrypt não seja enviado para o Django
       location /.well-known/acme-challenge/ {
           root /var/www/html;
       }

       # Repassa todo o restante para o Docker do Django (Porta 8002)
       location / {
           proxy_pass http://localhost:8002;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
4. Ative a configuração e reinicie:
   ```bash
   ln -s /etc/nginx/sites-available/risk_network /etc/nginx/sites-enabled/
   systemctl restart nginx
   ```

---

## 6. Geração do SSL (Cadeado Verde)

**Opção 1 (Padrão):**
```bash
certbot --nginx -d api.SEUDOMINIO.com
```

**Opção 2 (Standalone - Se o Nginx falhar com erro 500):**
Caso a rota do Nginx continue embaraçando, force o Certbot autônomo:
```bash
systemctl stop nginx
certbot certonly --standalone -d api.SEUDOMINIO.com
systemctl start nginx
```

---

## 7. Ajustes no Front-End (Vercel) e Erro 401
1. Após obter sucesso com o SSL, atualize as variáveis de ambiente na Vercel para a nova URL HTTPS (ex: `https://api.SEUDOMINIO.com`) e faça o **Redeploy**.
2. **Erro 401 Unauthorized:** 
   O Django REST Framework com `JWTAuthentication` barra conexões se o navegador enviar um Token JWT antigo no Cache/LocalStorage. Como o Token antigo não bate com a nova `SECRET_KEY` da VPS, o servidor recusa a conexão (mesmo na rota pública de registro).
   **Solução:** Fazer testes de navegação em uma **Guia Anônima** ou limpar o LocalStorage do navegador.
