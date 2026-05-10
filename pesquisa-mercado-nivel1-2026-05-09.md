---
pesquisa: RunTechOps — mercado BR de monitoramento/relatório de saúde e treinos com Garmin
nivel: 1 (varredura)
data: 2026-05-09
status: parcial — sessão Claude interrompida antes do Nível 2
sessao_origem: ec0fe98c-7ac1-443e-978a-8a8a2e9c8a0e
---

# Pesquisa de mercado — RunTechOps

## Prompt original

> Quero pesquisar o mercado de soluções de monitoramento/relatório de saúde e acompanhamento de treinos frente a um objetivo, usando a plataforma Garmin como fonte de informações. Aqui na pasta do projeto, estamos desenvolvendo a solução "RunTechOps" com esse objetivo. Me apresente um estudo do mercado atual para este tipo de solução no Brasil e suas possibilidades.

---

## Nível 1 — Varredura

Pesquisei 5 ângulos em paralelo. Resumo do que apareceu:

### 1. Players globais (incumbentes)

- **TrainingPeaks** continua dominante — PMC (TSS/CTL/ATL), integração nativa Garmin, é referência de mercado para coaches
- **Intervals.icu** — gratuito, virou alternativa séria (mais forte em ciclismo, mas crescendo em corrida)
- **Stryd** — potência na corrida, integra TrainingPeaks
- **Final Surge / Coachbox / Athlin / Today's Plan / Training Tilt / Good Coach App** — todos brigando como alternativas ao TrainingPeaks

### 2. Mercado brasileiro (players locais já operando)

| Player | Posicionamento |
|---|---|
| **Corrida Perfeita** | Líder nacional, +40% YoY, integra Garmin Coach |
| **Meu Treino AI** (meutreino.ai) | IA brasileira, planos personalizados |
| **Golden Runners** | IA + gamificação + personal humano |
| **Guerrinha IA** (TuTo) | 1º treinador IA Brasil via Strava+WhatsApp, parceria ultramaratonista |
| **RunMaps** | Em crescimento, propósito-driven |

**Tamanho do mercado:**
- Digital Fitness Brasil 2025: **US$ 1,32 bi**
- Health & Wellness Coaching Brasil 2025: **US$ 379 mi**
- Healthtechs ultrapassaram fintechs em número de startups no Brasil em 2025

### 3. Garmin como fonte de dados

- **Garmin Health API** (oficial) — push-based, OAuth 1.0a, dá Body Battery, HRV, sono, atividades — **MAS exige aprovação Garmin**, mais voltado pra empresas
- **Connect IQ SDK** — apps que rodam no relógio
- Caminho não-oficial: `garminconnect` (Python) — o que o RunTechOps deve estar usando
- Garmin Coach grátis embutido (mas limitado — Reddit reclama "cadê o Strength plan?")

### 4. AI Coaching (tendência mais quente 2025-2026)

- **Runna** (UK) — #1 rated, virou benchmark
- **TrainAsONE / Running Genie / PACE AI / RunRight / V AI** — todos com IA personalizada
- Mercado global: **US$ 22,36 bi (2026) → US$ 56,9 bi (2030), CAGR 26,3%**
- Diferencial competitivo declarado: adaptação semanal baseada em performance + integração relógio

### 5. Open source / DIY (onde RunTechOps mora hoje)

- **GoldenCheetah** — desktop, importa FIT direto
- **Intervals.icu** — web grátis com PMC
- **Projeto idêntico ao RunTechOps já existe nos fóruns Garmin:** *"self-hosted AI training advisor that sends you a daily Garmin report by email"* — exatamente sua proposta de valor
- **Self-hosted Grafana + Garmin + Docker + Python** — outro projeto público no dev.to

---

## Padrões emergentes

1. **Mercado explodindo** — CAGR 26%+ globalmente, healthtechs > fintechs no Brasil
2. **IA virou commodity esperada** — quem não tem em 2026, está atrás
3. **TrainingPeaks ainda é o "rei", mas cercado** — preço alto + UX antigo abrem espaço
4. **Brasil tem players locais relevantes mas fragmentados** — Corrida Perfeita, Meu Treino, Golden Runners, Guerrinha IA — nenhum ainda dominante
5. **Self-hosted/DIY é nicho real e crescendo** — RunTechOps tem "irmãos" no fórum Garmin

## Gaps (o que ainda não sei)

- Pricing real dos brasileiros (Corrida Perfeita, Meu Treino, Golden Runners)
- O que tecnicamente diferencia Corrida Perfeita do TrainingPeaks
- Tamanho específico do segmento "corredor amador com Garmin" no Brasil (não é todo o digital fitness)
- Modelo de negócio dominante (B2C assinatura? freemium? marketplace de coach?)
- Posição defensível de uma solução self-hosted/personalizada como RunTechOps

---

## Direções possíveis para o Nível 2 (análise comparativa)

**Sugiro escolher 1 destas três:**

**A. Foco competitivo BR** — Como Corrida Perfeita, Meu Treino AI, Golden Runners e Guerrinha IA se comparam entre si e com TrainingPeaks (preço, features, IA, integração Garmin). Te ajuda a posicionar o RunTechOps frente aos concorrentes diretos.

**B. Foco tecnológico/produto** — Comparativo de profundidade analítica: TrainingPeaks vs Intervals.icu vs Garmin Connect nativo vs solução self-hosted (RunTechOps-style). Te ajuda a entender que features são diferenciais reais e quais são commodity.

**C. Foco oportunidade de mercado** — Onde está o "white space" no Brasil para uma solução tipo RunTechOps: nicho vertical (maratonistas amadores?), B2B (treinadores?), open source (comunidade?). Te ajuda a decidir se RunTechOps deve virar produto.

---

## Complemento ao escopo (capturado em 2026-05-09 após o crash)

O RunTechOps **não é só monitoramento passivo** dos índices que o Garmin coleta. É também uma **camada de avaliação/julgamento** do estado atual de saúde e disposição, **confrontando**:

- dados Garmin (Body Battery, HRV, sono, carga, etc.)
- **objetivo declarado** pelo usuário (ex: meia em sub-1h45 daqui a 12 semanas)
- **treinos planejados/executados** rumo a esse objetivo

A pergunta que o app responde, no fundo, é: *"estou apto hoje a fazer o treino X, considerando meu objetivo Y e o que meus indicadores Z dizem sobre meu estado atual?"* — e por extensão, *"o plano ainda faz sentido frente ao que meu corpo está mostrando?"*

Isso muda o posicionamento competitivo: não é mais um *dashboard* (categoria de Intervals.icu, GoldenCheetah) nem um *plan generator* puro (Runna, Corrida Perfeita). É um **advisor / co-piloto** que cruza estado atual × plano × meta — categoria mais próxima de TrainingPeaks WKO (com o ATP/PMC) do que de qualquer player BR atual.

**Implicação para o Nível 2:** esse complemento pode tornar a direção **B (tecnológico/produto)** mais relevante, porque é onde aparece a diferença entre "mostrar dados" e "avaliar prontidão frente a um objetivo".
