# GeoRisk - Backend

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Django 6.0](https://img.shields.io/badge/django-6.0-092E20.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Uma rede social integrada com um sistema geoespacial de monitoramento de riscos climáticos extremos — inundações, tempestades, desmoronamentos, queimadas e geadas. Construída como Projeto Final do curso de Full Stack Python da EBAC.

---

## Sobre o Projeto

GeoRisk é uma plataforma focada em **comunicação rápida e geolocalizada** durante eventos climáticos. 
A ideia principal é unir um feed em tempo real com um mapa iterativo, onde os usuários podem reportar incidentes e acompanhar riscos na sua região e no Brasil inteiro.

O Backend foi estruturado utilizando a robustez do Django e do Django REST Framework para garantir uma API RESTful, escalável e segura.

---

## Funcionalidades Principais

- **Módulo Social (Feed & Usuários):**
  - Autenticação via JWT (`djangorestframework-simplejwt`).
  - Gerenciamento de Perfil (bio, foto de perfil/avatar).
  - Rede de Conexões (Follow / Unfollow).
  - Posts (Tweets), Curtidas e Comentários.
  - Feed Global e Feed Exclusivo de Seguidores.

- **Módulo GeoRisk (Mapa e Alertas):**
  - CRUD de Eventos Geoespaciais (GeoEvent).
  - Integração automática: Salvar um evento no mapa automaticamente cria um Post no feed para notificar a rede.
  - Captura precisa de latitude e longitude.

---

## Stack Tecnológica

- **Linguagem:** Python 3.13
- **Framework:** Django 6.0.7
- **API:** Django REST Framework 3.17
- **Autenticação:** djangorestframework-simplejwt 5.5
- **Banco de Dados:** SQLite (padrão)
- **Gerenciador de Pacotes:** Poetry

---

## Como Rodar o Backend Localmente

### 1. Clonar e Instalar
```bash
git clone <url-do-repositorio> risk_network_backend
cd risk_network_backend
poetry install
```

### 2. Configurar Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto contendo:
```dotenv
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
```

### 3. Migrar o Banco de Dados e Criar Superusuário
```bash
poetry run python manage.py migrate
poetry run python manage.py createsuperuser
```

### 4. Iniciar o Servidor
```bash
poetry run python manage.py runserver
```
A API estará rodando em `http://127.0.0.1:8000/`.

---

## Licença
Projeto distribuído sob a licença MIT. Veja o arquivo LICENSE para detalhes.
