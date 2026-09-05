# AquaSuíno — PRD

## Problem
Plataforma-piloto de gestão hídrica e de dejetos na suinocultura para o consórcio Produtor + Frivatti + Prefeitura. Mede consumo de água, monitora dejetos/biogás, gera alertas e prova viabilidade econômica.

## Personas & Views
- Produtor rural: gráfico consumo, meta, alertas, bônus estimado
- Frivatti: rede, ranking eficiência, adesão, bônus
- Prefeitura: KPIs agregados, propriedades, retorno econômico, PDF de viabilidade

## Requirements (core)
- 3 dashboards distintos (role selector no header)
- Cadastro de propriedade + hidrômetro
- Leitura manual mensal com foto opcional (object storage)
- Módulo dejetos/biogás (fator Embrapa 0.062 m³/kg)
- Alertas automáticos (consumo alto / meta atingida)
- PDF de viabilidade (peça-chave do pitch)
- Seed com 10 propriedades × 10 meses

## Tech Stack
FastAPI + Motor/MongoDB + Recharts + Tailwind + ReportLab (PDF) + Emergent Object Storage

## Implemented (2026-02)
- Backend: /api/propriedades, /api/leituras (multipart+foto), /api/dejetos, /api/alertas, /api/dashboard/frivatti, /api/dashboard/prefeitura, /api/relatorio/viabilidade (PDF), /api/seed
- Seed script (10 propriedades, 10 meses de leituras, dejetos, alertas)
- Frontend: Landing (hero + 4 passos + 3 perfis), Header role selector, ProdutorDashboard (KPIs+charts+dialogs), FrivattiDashboard (ranking+table), PrefeituraDashboard (KPIs+pie+grid)
- PDF ReportLab com KPIs, tabela de propriedades, metodologia, riscos

## Backlog / Roadmap
P1: Auth JWT com 3 roles (produtor/frivatti/prefeitura), convite Frivatti → produtor, isolamento de dados
P1: IoT endpoint pronto pra hidrômetro conectado (webhook)
P2: Mapa interativo (Leaflet) das propriedades na Prefeitura
P2: Email alerts via Resend
P2: Roteiro de fala do pitch dividido por integrante
P2: Simulação de expansão (50/100 propriedades)
