Ran command: `cd d:\2026\S\EBAC\BACKEND\Projeto_Final\social_network`

Como estamos construindo uma **API Backend** (que não tem interface gráfica própria além da administrativa), acessar a raiz `http://127.0.0.1:8000/` retorna erro 404 porque não definimos nenhuma página inicial (o que é normal, pois o Front-end fará esse papel futuramente).

A boa notícia é que o **Django REST Framework (DRF)** possui uma interface web nativa para testarmos a API diretamente pelo navegador! 

Siga este passo a passo para testar usando o próprio navegador:

### Passo 1: Criar um Usuário (Registrar)
1. Acesse: http://127.0.0.1:8000/api/users/auth/register/
2. Você verá uma página do DRF com um formulário no final.
3. Preencha `username`, `email`, e `password` com dados fictícios (ex: user `joao`, email `joao@teste.com`, senha `senha123`).
4. Clique no botão **POST**. Você verá a resposta de sucesso criando o usuário.
5. Faça isso mais uma vez para criar um segundo usuário (ex: `maria`).

### Passo 2: Fazer Login (Gerar o Token JWT)
1. Acesse: http://127.0.0.1:8000/api/users/auth/login/
2. No formulário inferior, insira o `username` e `password` de um dos usuários que você criou.
3. Clique em **POST**. 
4. A resposta mostrará dois códigos longos: o `refresh` e o `access` token. (Esse `access` token é a "chave" que o frontend usará para provar quem está logado).

### Passo 3: O Painel de Administração (Admin)
O Django já vem com um painel pronto para gerenciarmos o banco de dados.
1. Antes de acessá-lo, crie um superusuário no terminal do VSCode. Abra um novo terminal (+), navegue até a pasta e rode:
   `poetry run python manage.py createsuperuser`
   (Siga as instruções para criar admin/admin)
2. Acesse no navegador: http://127.0.0.1:8000/admin/
3. Faça login com o superusuário criado.
4. Lá dentro você verá as tabelas de `Users`, `Tweets`, `Likes` e `Comments`. Você pode criar tweets e manipular os dados diretamente por lá de forma visual!

### Testando rotas autenticadas (Postman ou Insomnia)
A interface do navegador não permite injetar o token JWT facilmente. Para testar coisas como "Criar Tweet" ou "Seguir", recomendo usar o **Postman**, **Insomnia** ou a extensão **Thunder Client** (se estiver usando VSCode). 
Nesses programas:
1. Você faz a rota `POST` de Login para pegar o Token.
2. Nas rotas protegidas (ex: `GET http://127.0.0.1:8000/api/tweets/`), você adiciona um cabeçalho (Header):
   - Key: `Authorization`
   - Value: `Bearer SEU_ACCESS_TOKEN_AQUI`

Tente o **Passo 1** e **Passo 3** primeiro pelo navegador para ver as informações entrando no banco de dados! O que acha?



=========================================
Teste final : 
poetry run python manage.py createsuperuser
Username: admin
Email address: admin@gmail.com
Password: 
Password (again): 
Superuser created successfully.