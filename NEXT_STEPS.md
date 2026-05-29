# Next Steps — site-auditor (API)

## Alta prioridade

- [ ] **Autenticação por API Key**
  Proteger o endpoint `/audit` com uma chave via header `X-API-Key`.
  Evita uso não autorizado quando o serviço estiver público no Railway.

- [ ] **Rate limiting**
  Limitar requisições por IP ou por API key (ex: 60 req/min).
  Biblioteca: `slowapi`.

- [ ] **Endpoint `/audit/sitemap`**
  Receber uma URL de sitemap, extrair as URLs e auditar todas em paralelo.
  Retornar lista de resultados com score por página.
  Útil para integração direta sem precisar do dashboard.

- [ ] **Processamento assíncrono com job ID**
  Para sitemaps grandes, retornar um `job_id` imediatamente e expor
  `GET /audit/job/{id}` para consultar o resultado quando estiver pronto.

## Médio prazo

- [ ] **Persistência dos resultados**
  Salvar cada auditoria em banco (PostgreSQL via Railway) para histórico e comparação.

- [ ] **Mais verificações de SEO**
  - Dados estruturados (JSON-LD / Schema.org)
  - Open Graph completo (og:image, og:url)
  - Hreflang para páginas multilíngue
  - Tamanho do HTML (páginas muito pesadas)
  - Detecção de conteúdo duplicado entre páginas

- [ ] **Verificação de links quebrados**
  Checar se links internos e externos retornam 2xx.

- [ ] **Suporte a headers customizados**
  Permitir passar cookies ou headers de autenticação para auditar páginas protegidas.

## Futuro

- [ ] **Webhook**
  Notificar uma URL externa quando uma auditoria terminar (útil para CI/CD).

- [ ] **Cache de resultados**
  Evitar re-auditar a mesma URL em menos de N minutos.

- [ ] **Score ponderado por tipo de página**
  Páginas de produto vs. blog vs. home têm pesos diferentes para cada issue.
