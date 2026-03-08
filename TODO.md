# TODO — Próximas fases da plataforma

## Fase 2 — Coleta pública (com autenticação)

- [ ] Definir provedor de autenticação (Google + e-mail mágico)
- [x] Implementar modelo de usuários e sessões
- [ ] Criar fluxo de assinatura autenticada
- [ ] Registrar consentimento e política de privacidade

## Fase 3 — Defesas e participação

- [ ] Criar módulo de defesas (texto curto)
- [ ] Criar sistema de curtir/upvote
- [ ] Definir moderação mínima (filtro e revisão)

## Fase 4 — Persistência e painel

- [ ] Escolher banco de dados para produção
- [x] Implementar migrations
- [ ] Criar painel administrativo para datas de vagas e conteúdo
- [ ] Auditoria de alterações no painel

## Fase 5 — Segurança e resiliência

- [ ] Integrar Cloudflare WAF (rules + bot protection)
- [ ] Definir rate limiting por rota crítica
- [ ] Configurar estratégia de cache por tipo de conteúdo
- [ ] Revisar headers de segurança (CSP, HSTS, etc.)

## Fase 6 — Métricas e operação

- [x] Instrumentar analytics de campanha (GA4 básico)
- [ ] Monitorar disponibilidade e erro (APM/logging)
- [ ] Definir checklist de release e rollback
