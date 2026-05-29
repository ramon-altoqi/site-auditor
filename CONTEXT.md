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
