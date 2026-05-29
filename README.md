# site-auditor

Serviço de auditoria técnica de SEO para URLs públicas. Audita uma página por requisição e retorna issues classificadas por severidade, score e dados estruturados.

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Documentação interativa (Swagger UI) |
| `POST` | `/audit` | Audita uma URL |

---

## Como rodar localmente

### Pré-requisitos

- Python 3.11+

### Instalação

```bash
cd site-auditor

# Criar ambiente virtual (recomendado)
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### Executar

```bash
python main.py
```

O servidor sobe em `http://localhost:3000`.

A documentação interativa fica em `http://localhost:3000/docs`.

---

## Como testar com curl

### Health check

```bash
curl http://localhost:3000/health
```

### Auditar a homepage da AltoQi

```bash
curl -s -X POST http://localhost:3000/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.altoqi.com.br/home"}' | python -m json.tool
```

### Auditar qualquer URL

```bash
curl -s -X POST http://localhost:3000/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://exemplo.com/pagina"}' | python -m json.tool
```

### Testar erros

```bash
# URL inválida
curl -s -X POST http://localhost:3000/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "nao-e-uma-url"}'

# Sem campo url
curl -s -X POST http://localhost:3000/audit \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Formato do retorno

```json
{
  "success": true,
  "url": "https://www.altoqi.com.br/home",
  "status_code": 200,
  "audited_at": "2024-01-15T12:00:00+00:00",
  "score": 76,
  "summary": { "critical": 0, "warning": 3, "info": 1 },
  "seo": {
    "title": { "value": "AltoQi | Software para Engenharia", "length": 33 },
    "meta_description": { "value": "...", "length": 120 },
    "canonical": "https://www.altoqi.com.br/home",
    "robots": null,
    "open_graph": { "title": "...", "description": "..." },
    "headings": {
      "h1": ["Título principal"],
      "h2": ["Subtítulo 1", "Subtítulo 2"]
    }
  },
  "links": {
    "internal": { "count": 15, "items": [...] },
    "external": { "count": 4, "items": [...] },
    "without_text": { "count": 2, "items": [...] }
  },
  "images": {
    "without_alt": { "count": 3, "items": [...] }
  },
  "issues": [
    {
      "severity": "warning",
      "code": "LINKS_WITHOUT_TEXT",
      "message": "7 link(s) sem texto âncora visível",
      "details": { "count": 7, "sample": [...] }
    }
  ]
}
```

### Severidades das issues

| Severidade | Penalidade no score | Exemplos |
|------------|--------------------|----------------------------------------------------|
| `critical` | −20 pts | Sem title, sem H1, noindex, sem meta description |
| `warning` | −8 pts | Title/description fora do tamanho, imagens sem alt |
| `info` | −2 pts | Ausência de H2 |

### Códigos de erro HTTP da API

| Status | Tipo | Causa |
|--------|------|-------|
| 422 | `INVALID_URL` | URL malformada ou sem protocolo http/https |
| 422 | `NOT_HTML` | URL retorna conteúdo não-HTML |
| 504 | `TIMEOUT` | Timeout ao buscar a página |
| 502 | `DNS_ERROR` | Host não encontrado |
| 502 | `HTTP_ERROR` | Página retornou 4xx/5xx |

---

## Deploy no Railway

### Via CLI

```bash
# Instalar Railway CLI
npm install -g @railway/cli   # ou: brew install railway

railway login
railway init       # dentro da pasta do projeto
railway up
```

### Via GitHub

1. Faça push do repositório para o GitHub
2. Acesse [railway.app](https://railway.app) e crie um novo projeto
3. Selecione "Deploy from GitHub repo"
4. O Railway detecta o `requirements.txt` e usa Python automaticamente

O comando de start é detectado automaticamente via `main.py`. Caso precise configurar manualmente, use:

```
python main.py
```

### Variáveis de ambiente no Railway

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `PORT` | `3000` | Porta do servidor (Railway injeta automaticamente) |
| `REQUEST_TIMEOUT_MS` | `10000` | Timeout em ms para fetch das páginas |

---

## Variáveis de ambiente locais

```bash
cp .env.example .env
```

```env
PORT=3000
REQUEST_TIMEOUT_MS=10000
```
