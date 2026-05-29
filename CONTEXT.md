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
| product-watcher | 💡 Fonte a definir | Monitora onde o time de produto publica novas versões de software |
| webflow-publisher | 📋 Planejado | Publica/atualiza itens no CMS do Webflow via API |
| hubspot-publisher | 📋 Planejado | Publica posts no blog do HubSpot E atualiza formulários de lead |
| orchestrator | 📋 Planejado | Recebe intenção do usuário via LLM e roteia para o agente correto |
| blog-writer | 💡 Fora do MVP atual | Gera rascunhos de posts dado tema, referências e tom de voz |

---

### Fluxo de lançamento de nova versão de software

Contexto: quando o time de produto lança uma nova versão, o time de marketing precisa
manualmente (1) atualizar o CMS do Webflow e (2) atualizar o link do instalador no HubSpot.
O objetivo é automatizar esse fluxo com aprovação humana antes da publicação final.

```
[Fonte do time de produto]  ← ainda a definir (ver abaixo)
        ↓  crawler detecta nova versão + URL do instalador
[product-watcher]
        ↓  normaliza os dados (produto, versão, data, URL do instalador)
   ┌────┴──────────────────────────────┐
   ↓                                   ↓
[webflow-publisher]            [hubspot-updater]
  Cria/atualiza item no CMS:     Atualiza redirect URL
  - Página de novidades          do formulário de lead
  - Página de downloads          via HubSpot Forms API v3
  (publica em staging)

        ↓  envia notificação (Slack ou e-mail)
[Aprovação humana]
  Resumo: "Nova versão detectada: AltoQi RMS 2024-12
           Publicado em staging. Aprovar para produção?"
        ↓  clique confirma
  - Webflow: promove staging → produção
  - HubSpot: atualiza o redirect URL do formulário
```

#### Detalhes técnicos já mapeados

**Webflow CMS (webflow-publisher)**
- O Webflow do site da AltoQi usa CMS (não páginas estáticas) — tem API oficial
- É possível criar e atualizar itens de coleção via `POST/PATCH /collections/{id}/items`
- Páginas alvo: novidades e downloads
- Publicação em staging primeiro, promoção para produção mediante aprovação

**HubSpot (hubspot-publisher) — um serviço, duas responsabilidades**
- `POST /hubspot/blog` → cria/edita post no blog do HubSpot
- `PATCH /hubspot/form/{id}` → atualiza redirect URL do formulário de lead
- Compartilham autenticação e cliente HTTP — não justifica dois serviços separados
- Formulário: campo "redirecionar para URL externo" nas Opções do formulário
- URL atual de exemplo: `https://cdn.altoqi.com.br/AltoQi/AltoQi_2024-12_RMS.exe`
- API de forms: `PATCH /marketing/v3/forms/{formId}` com API key do HubSpot
- Atualização do form só ocorre após aprovação humana

**Aprovação humana**
- Após publicar em staging, o serviço envia notificação com resumo das mudanças
- A aprovação pode ser um botão no dashboard Streamlit ou um link direto na notificação
- Somente após aprovação o webflow-publisher promove para produção e o hubspot-updater executa

**Fonte do time de produto (product-watcher)**
- Ainda não definida — precisa ser alinhada com o time de produto
- Pode ser: Notion, planilha Google, página interna, canal Slack, e-mail, etc.
- Cada fonte exige uma estratégia de crawler diferente — definir antes de implementar

---

### Extensões planejadas para o site-auditor

Antes de novos serviços, há melhorias de alto valor no que já existe:

- **Core Web Vitals** — integrar Google PageSpeed Insights API (gratuita) para trazer LCP, CLS e FID direto no retorno do `/audit`
- **Links quebrados** — verificar status HTTP de cada link interno encontrado, reportar 404s
- **Histórico de scores** — persistir resultados no Supabase (free tier suficiente: 500MB para dezenas de milhares de auditorias)

---

### Padrão orquestrador

Para compor os agentes de forma inteligente, o padrão é um **orquestrador LLM** que recebe a intenção do usuário em linguagem natural e decide qual agente acionar.

```
[Usuário digita no dashboard]
  ex: "publica post sobre BIM no blog"
  ex: "atualiza o instalador do Visus para 2025-01"
        ↓
[Orquestrador — Claude API com tool use]
  Entende intenção, extrai entidades,
  decide qual(is) agente(s) acionar
        ↓              ↓               ↓
[webflow-publisher] [hubspot-publisher] [blog-writer]
```

Cada agente especializado vira uma "tool" disponível para o orquestrador. O orquestrador não executa nada diretamente — apenas roteia e coordena.

---

### Agente de redação de blog (blog-writer)

Fora do MVP atual, mas se encaixa naturalmente na plataforma:

```
[Usuário] → tema + referências (URLs) + tom de voz
    ↓
[site-auditor]  ←  audita as URLs de referência
    ↓  dados SEO + estrutura das páginas concorrentes
[blog-writer — Claude API]
  Gera rascunho contextualizado
    ↓
[Revisão humana no dashboard]
    ↓ aprovação
[hubspot-publisher → POST /hubspot/blog]
```

O `site-auditor` já existente alimenta o `blog-writer` com dados das páginas que se quer superar no ranking — auditoria técnica vira insumo para produção de conteúdo.

---

### Composição futura

Com todos os serviços rodando, automações possíveis:
- "Novo software lançado → atualizar Webflow + HubSpot → auditar a página → alertar se score < 80"
- "Toda semana → rodar sitemap completo → comparar score com semana anterior → notificar regressões"
- "Usuário informa tema → blog-writer gera rascunho → revisão → hubspot-publisher publica"

Cada serviço permanece independente e testável isoladamente. A composição acontece via orquestrador LLM ou via chamadas HTTP diretas entre serviços.
