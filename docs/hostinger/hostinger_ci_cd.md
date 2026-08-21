# Guia de Configuração CI/CD: GitHub Actions para Hostinger VPS

A integração contínua e entrega contínua (CI/CD) permite que toda vez que você der um `git push` para a branch `main` no GitHub, o seu servidor VPS na Hostinger seja atualizado automaticamente, sem precisar acessar o terminal SSH.

Para este projeto rodando em Docker, a maneira mais profissional e gratuita de fazer isso é utilizando o **GitHub Actions**.

---

## 1. O que precisaremos fazer? (Resumo do Trabalho)

- **Esforço Estimado:** Baixo/Médio (cerca de 30 minutos).
- **Custo:** Zero (o GitHub Actions é gratuito para repositórios públicos e tem uma cota generosa para privados).
- **Onde mexer:**
  1. Painel da Hostinger (VPS) / Terminal SSH (para criar chaves SSH).
  2. Configurações do Repositório no GitHub (para salvar as chaves e senhas com segurança).
  3. Código da aplicação (criar um arquivo YAML definindo os passos do deploy).

---

## 2. Passo a Passo Detalhado

### Passo 1: Preparar a VPS para receber acessos do GitHub Actions
O GitHub precisa de uma "chave mágica" para entrar no seu servidor sem pedir senha, exatamente como você faz via SSH, mas de forma automatizada.

1. Acesse a VPS via SSH (como você sempre faz).
2. Gere um novo par de chaves SSH dedicado para o GitHub Actions executando:
   ```bash
   ssh-keygen -t ed25519 -C "github-actions-deploy"
   ```
   *(Pressione Enter para todas as perguntas, **não** coloque senha/passphrase na chave).*
3. Adicione a chave pública recém-criada ao arquivo de permissões da VPS:
   ```bash
   cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
   ```
4. Exiba a chave **PRIVADA** na tela e copie todo o texto (do `-----BEGIN` até o `END-----`):
   ```bash
   cat ~/.ssh/id_ed25519
   ```

### Passo 2: Configurar os "Secrets" no GitHub
Por questões de segurança, você nunca deve colocar a chave privada, IPs ou senhas no código. Usamos os Secrets do GitHub.

1. Vá até o seu repositório no GitHub.
2. Clique em **Settings** > **Secrets and variables** > **Actions**.
3. Clique em **New repository secret** e adicione os seguintes secrets um por um:
   - `VPS_HOST`: O IP da sua Hostinger (ex: `187.77.61.11`).
   - `VPS_USER`: O usuário SSH (geralmente `root`).
   - `VPS_SSH_KEY`: Cole aqui a chave **privada** que você copiou no Passo 1.

### Passo 3: Criar o Workflow do GitHub Actions
Agora que o GitHub tem a chave do servidor, precisamos dizer a ele quais comandos rodar (os mesmos que fizemos manualmente hoje).

1. No seu computador, abra o repositório `risk_network_backend`.
2. Crie uma pasta chamada `.github` e, dentro dela, uma subpasta chamada `workflows`.
3. Crie um arquivo chamado `deploy.yml` (`.github/workflows/deploy.yml`).
4. Adicione o seguinte conteúdo no arquivo:

```yaml
name: Deploy to Hostinger VPS

on:
  push:
    branches:
      - main # O deploy acontecerá sempre que houver push na main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            # Entra na pasta do projeto
            cd /root/risk_network_backend
            
            # Puxa o código novo
            git pull origin main
            
            # Reconstrói a imagem Docker e sobe o container
            docker compose up -d --build
            
            # Aplica novas migrações automaticamente (se houver)
            docker exec risk_network_backend-web-1 python manage.py migrate
```

### Passo 4: Testar o CI/CD
Para testar se funcionou, basta fazer um commit de qualquer alteração besta (como um novo comentário no código) e dar `git push`.
1. Vá até a aba **Actions** no seu repositório no GitHub.
2. Você verá uma "bolinha amarela" indicando que o deploy começou.
3. Se ela ficar **Verde**, significa que o GitHub acessou sua Hostinger, puxou o código e restartou o Docker automaticamente!

---

## 3. O que acontece após configurar isso?
Sempre que você, ou qualquer desenvolvedor da equipe, enviar uma alteração para a branch `main` (`git push origin main`), o sistema entrará na Hostinger e rodará os passos de pull, build e migrate automaticamente. Isso garante que o servidor estará sempre sincronizado com o GitHub, prevenindo erros humanos de esquecer de aplicar as migrations (que geraram o Erro 500 de hoje).
