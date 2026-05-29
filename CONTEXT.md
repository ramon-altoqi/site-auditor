# Contexto do Projeto — Site Auditor

## O que é

Sistema de auditoria técnica de SEO composto por dois serviços independentes:

- **site-auditor** — API REST em Python (FastAPI). Recebe uma URL e retorna uma auditoria técnica da página.
- **site-auditor-ui** — Dashboard em Python (Streamlit). Interface para o time de marketing/dev usar a API sem precisar de curl.

## Objetivo

Auditar páginas do site da AltoQi (atualmente em Webflow) e identificar issues de SEO priorizadas por severidade. O serviço é genérico e funciona com qualquer site público.

## Stack

| Serviço | Linguagem | Framework | Deploy |
|---------|-----------|-----------|--------|
| site-auditor | Python 3.11+ | FastAPI + uvicorn | Railway |
| site-auditor-ui | Python 3.11+ | Streamlit | Railway (a fazer) |

Dependências principais: `requests`, `beautifulsoup4`, `lxml`, `pydantic`.

## Repositórios

- API: https://github.com/ramon-altoqi/site-auditor
- UI: https://github.com/ramon-altoqi/site-auditor-ui

## Estrutura dos arquivos

### site-auditor (API)
```
site-auditor/
├── main.py         # FastAPI: rotas /health e /audit
├── auditor.py      # Lógica: fetch, parse HTML, extração, issues, score
├── requirements.txt
├── Procfile        # web: python main.py
└── .env.example
```

### site-auditor-ui (Dashboard)
```
site-auditor-ui/
├── app.py          # Streamlit: aba de URL única + aba de sitemap
├── sitemap.py      # Parser de sitemap.xml (inclui sitemap index)
├── requirements.txt
├── Procfile        # web: streamlit run app.py --server.port=$PORT ...
└── .env.example
```

## O que a API faz

`POST /audit` com `{"url": "https://..."}` retorna:

- **score** (0–100): pontuação calculada com base nas issues encontradas
- **seo**: title, meta description, canonical, robots, Open Graph, H1s, H2s
- **links**: internos, externos, sem texto âncora
- **images**: imagens sem atributo alt
- **issues**: lista de problemas classificados por severidade

### Severidades e penalidades
| Severidade | Penalidade | Exemplos |
|------------|-----------|---------|
| critical | −20 pts | Sem title, sem H1, noindex, sem meta description |
| warning | −8 pts | Title/description fora do tamanho ideal, imagens sem alt |
| info | −2 pts | Ausência de H2 |

### Outros endpoints
- `GET /health` — health check
- `GET /docs` — Swagger UI gerado automaticamente pelo FastAPI

## O que o dashboard faz

- **Aba "Auditar página"**: input de URL → chama `POST /audit` → exibe score, issues, dados SEO
- **Aba "Auditar via Sitemap"**: input de URL do sitemap → carrega todas as URLs → seleção via multiselect → audita as selecionadas em sequência → exibe tabela comparativa + detalhes por página

## Variáveis de ambiente

### site-auditor
| Variável | Padrão | Descrição |
|----------|--------|-----------|
| PORT | 3000 | Injetado automaticamente pelo Railway |
| REQUEST_TIMEOUT_MS | 10000 | Timeout por requisição de página |

### site-auditor-ui
| Variável | Padrão | Descrição |
|----------|--------|-----------|
| PORT | 8501 | Injetado automaticamente pelo Railway |
| AUDITOR_URL | http://localhost:3000 | URL base da API site-auditor |

## Status atual

- [x] API implementada e funcionando localmente
- [x] API deployada no Railway (Online)
- [x] Dashboard implementado e testado localmente
- [ ] Dashboard deployado no Railway
- [ ] Autenticação por API key
- [ ] Endpoint `/audit/sitemap` direto na API

## Próximos passos planejados

Ver `NEXT_STEPS.md` em cada repositório para o roadmap detalhado. Prioridades imediatas:
1. Deploy do dashboard (site-auditor-ui) no Railway
2. Autenticação por API key na API
3. Endpoint `/audit/sitemap` para integração direta sem UI

---

## Visão maior — Plataforma de microserviços de marketing

O site-auditor é o primeiro serviço de uma plataforma maior. A ideia central é:
**cada serviço faz uma coisa bem definida, expõe uma API HTTP, e pode ser composto com os demais.**

O mesmo padrão (FastAPI + Railway + Streamlit para UI interna) se aplica a qualquer fonte de dados ou automação de marketing.

### Serviços mapeados ou em discussão

| Serviço | Status | O que faz |
|---------|--------|-----------|
| site-auditor | ✅ Em produção | Audita qualidade técnica de SEO de uma página |
| site-auditor-ui | 🔧 Em desenvolvimento | Dashboard para usar o site-auditor visualmente |
| product-tracker | 💡 A definir | Coleta informações sobre publicações de novos softwares/versões feitas pelo time de produto — ainda sem fonte de dados definida |

### Sobre o product-tracker

O time de produto da AltoQi publica informações sobre softwares em algum canal que o time de marketing ainda não tem visibilidade total. A ideia é criar um serviço que:
- Monitore esse(s) canal(is) de publicação
- Normalize as informações coletadas (nome do produto, versão, data, descrição)
- Exponha uma API para que outros serviços (ou o dashboard) consumam esses dados

A fonte de dados e o formato ainda precisam ser investigados com o time de produto antes de começar a implementação.

### Composição futura

Com múltiplos serviços rodando, é possível criar automações como:
- "Quando um novo software for publicado → auditar a página do produto no site → alertar se o score de SEO estiver abaixo de 80"
- "A cada semana → rodar o sitemap completo → comparar score com semana anterior → notificar regressões"
- "Detectar que uma página foi atualizada no Webflow → disparar auditoria automática"

Cada serviço permanece independente e testável isoladamente — a composição acontece via chamadas HTTP entre eles ou via um orquestrador simples.
