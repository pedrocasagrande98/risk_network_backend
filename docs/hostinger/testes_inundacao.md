# Guia Completo: Testes e Execução do Motor de Inundação (GeoRisk)

Este guia foi criado para que você possa iniciar uma **nova conversa limpa** e ter total controle sobre a inicialização e os testes do ecossistema, agora que todos os bugs estruturais (cross-stealing de filas Celery e parsing de FeatureCollection) foram resolvidos.

---

## 1. Status Atual
**TODOS os servidores e tarefas em background foram derrubados com sucesso.** 
No momento, o ambiente está **100% offline** e seguro para uma reinicialização do zero.

---

## 2. Preparação: Banco de Mensagens (Redis)

O ecossistema depende do Redis para orquestrar as filas do Celery.
Caso não tenha um Redis rodando nativamente ou no WSL, você pode subi-lo facilmente usando Docker:
```powershell
docker run -d -p 6379:6379 --name redis_broker redis
```
*(Nota: O código agora está otimizado para não haver conflito de filas. O Django usa o banco `0`, o WTH usa o banco `1`, e o OSMNX usa o banco `2` do Redis).*

---

## 3. Como Ligar os Servidores (Ordem Recomendada)

Recomendamos abrir terminais separados (ou usar abas no VSCode) para rodar cada um dos serviços abaixo. 

### A. Motor WTH (Inundação)
1. **API (FastAPI)**:
   ```powershell
   cd WTH_MOTOR_VALIDATE
   ..\.venv\Scripts\python -m uvicorn main:app --port 8001 --reload
   ```
2. **Worker Celery**:
   ```powershell
   cd WTH_MOTOR_VALIDATE
   ..\.venv\Scripts\celery -A worker.celery_app worker -l info --pool=solo
   ```

### B. Extrator OSMNX (Vias)
3. **API (FastAPI)**:
   ```powershell
   cd osmnx_street
   ..\.venv\Scripts\python -m uvicorn main:app --port 8002 --reload
   ```
4. **Worker Celery**:
   ```powershell
   cd osmnx_street
   ..\.venv\Scripts\celery -A worker.celery_app worker -l info --pool=solo
   ```

### C. Orquestrador Backend (Django)
5. **API (Django)**:
   ```powershell
   cd risk_network_backend
   ..\.venv\Scripts\python manage.py runserver 8000
   ```
6. **Worker Celery**:
   ```powershell
   cd risk_network_backend
   ..\.venv\Scripts\celery -A core worker -l info --pool=solo
   ```

### D. Frontend (Vite/React)
7. **Servidor de Interface**:
   ```powershell
   cd risk_network_frontend
   npm run dev
   ```

---

## 4. Como Testar

Com tudo ligado, você tem duas opções para validar se o fluxo ponta a ponta (Frontend -> Django -> WTH -> Django -> OSMNX -> Django -> Frontend) está 100% funcional:

### Opção 1: Teste Automatizado E2E (Via Script)
Foi criado um script na raiz do projeto (`test_e2e_flood_flow.py`) que faz login como `twitter9`, posta o evento, aguarda o Celery processar as duas inteligências artificiais e valida o resultado final.

Abra um terminal na raiz do projeto e execute:
```powershell
.\.venv\Scripts\python test_e2e_flood_flow.py
```
*Se a saída finalizar com `✅ TESTE E2E APROVADO`, os microserviços estão integrados com sucesso.*

### Opção 2: Teste Visual (Via Interface Gráfica)
1. Acesse `http://localhost:5173` no seu navegador.
2. Faça login (usuário: `twitter9`, senha: `twitter9999`).
3. Vá até o mapa/registro de evento.
4. **IMPORTANTE**: Para garantir que o WTH encontre água e dispare a extração de ruas, clique ou informe uma coordenada próxima à **Avenida do Estado / Rio Tamanduateí**.
   - Latitude Sugerida: `-23.593717`
   - Longitude Sugerida: `-46.564531`
5. Registre o evento ("Inundacao" / "Critica").
6. Acompanhe na tela o botão ficar em processamento e, em poucos segundos, a mensagem de sucesso deve aparecer junto do desenho do polígono azul e as linhas vermelhas das vias bloqueadas.
