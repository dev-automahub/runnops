# Protocolo de Recuperação e Performance — 21K em 06/06/2026

**Data:** 2026-05-04 | **Janela até a prova:** 33 dias | **Atleta:** masculino, 54 anos, 1,90m, 98 kg (IMC 27,1)
**Volume atual:** 30-45 km/semana corrida + **3× força/sem (seg/qua/sex, 1h cada)** | **FCrep 51 bpm** | **Sem histórico de lesão**
**Plataformas:** Garmin Connect + TrainingPeaks Premium

> ⚠️ **Atenção — este relatório cobre o 21K #1 (06/06) dentro de uma temporada maior.**
> Provas no horizonte: 21K #1 em 06/06 → 21K #2 em 26/07 → **Maratona em 30/08 (meta 4h30)**.
> Para a visão completa da temporada de 17 semanas, ver `macrociclo.md` na mesma pasta.
> Este relatório foi ajustado para o 21K #1 ser rodado **a 90% do esforço** (não PR), preservando reserva para o bloco maratoniano que vem na sequência.

---

## Resumo Executivo

Você está com **TSB +39, CTL 31, ATL 14**. Isso significa que está **fresco demais** (TSB > +25 = perda de fitness por destreino) e com base aeróbia menor do que o ideal para 21K (CTL ideal 45-60). Em 33 dias dá para construir até **CTL 42-46** com ramp +5/semana, taperizar nos últimos 12-14 dias e chegar com **TSB +8 a +10** na largada.

**Tempo-alvo realista para 06/06 — estratégia "long run forte controlado a 90%":**
- Pace alvo: **6:30-6:35/km**
- Tempo esperado: **2h18-2h22** (terminar confortável, sem esgotar)
- **NÃO atacar PR aqui.** Toda reserva preservada vale ouro no bloco maratoniano que vem em seguida (07/06 → 26/07).

**Por que a 90% e não a 100%:**
- 21K #2 em 26/07 (50 dias depois) é a prova que valida sua meta de 4h30 na maratona — ali atacar tempo
- Esgotar no #1 custa 7-10 dias de bloco 2 (caro demais)
- Maratona 30/08 é a meta principal da temporada

**Os 5 pilares deste protocolo:**
1. Periodização: Build 18 dias + Taper 15 dias
2. Recuperação multimodal (sono > nutrição > modalidades)
3. Nutrição calibrada para 98 kg (proteína 156-196 g/d, carbo 5-10 g/kg/d conforme fase)
4. Força/core 2x/semana mantidos durante taper (ajustando carga)
5. Sistema técnico Python para decisão diária baseada em HRV + Body Battery + TSB

**Confiança das recomendações:** Alta para periodização, nutrição e modalidades de recuperação (consenso entre Daniels/Friel/Magness, ISSN, ACSM). Média para o stack técnico (APIs oficiais Garmin/TrainingPeaks são restritas; soluções via libs não oficiais funcionam mas são frágeis).

---

## 1. Diagnóstico de Performance

### 1.1. Leitura dos seus números

| Métrica | Valor | Faixa de referência | Interpretação |
|---|---|---|---|
| TSB | **+39** | -10 a +20 (treino) / +5 a +15 (prova) | **"Fresco demais"** — sinal de destreino |
| CTL | **31** | 45-60 para 21K amador | **Baixo** — base aeróbia ainda em construção |
| ATL | **14** | ~CTL em fase de carga | Confirma desaceleração recente |
| FCmáx Tanaka (54a) | **170 bpm** | — | Base para zonas |
| FCrep | **51 bpm** | <60 ótimo p/ 54a | Excelente base cardiovascular |
| FC longão 17K | **140 bpm** | — | **75% FCR (Karvonen) = Z3 médio**, não Z2 |
| Pace longão | **6:33/km** | — | Coerente com VO2máx ~38-42 ml/kg/min |
| IMC | **27,1** | <25 normal | Sobrepeso classe 1 — fator de impacto |

### 1.2. Zonas de FC (Karvonen com FCrep 51 confirmada)

FCR = FCmáx (170) − FCrep (51) = **119 bpm**

| Zona | %FCR | bpm = 51 + (% × 119) | Pace estimado | Quando usar |
|---|---|---|---|---|
| Z1 — Recuperação | 50-60% | **111-122** | 7:30-8:00 | Regenerativo, walk-jog |
| **Z2 — Aeróbio base** | 60-70% | **122-134** | **6:55-7:15** | **Longão verdadeiro** |
| Z3 — Limiar aeróbio | 70-80% | **134-146** | 6:25-6:50 | Tempo run, ritmo médio |
| Z4 — Limiar anaeróbio | 80-90% | **146-158** | 5:50-6:10 | Threshold, prova 10K |
| Z5 — VO2máx | 90-100% | **158-170** | 5:15-5:30 | Intervalos curtos |

**Achado crítico:** seu longão de 17K a 140 bpm está em **Z3 médio**, não em Z2. Isso explica o TSB +39 paradoxal — você corre intensidade alta em volume insuficiente, gerando ATL sem CTL. **Alvo de longão Z2 verdadeiro: 125-132 bpm**, mesmo que o pace caia para 7:00-7:15/km. FCrep 51 é excelente — sua base cardiovascular é melhor do que o CTL sugere.

### 1.3. Projeção 21K (06/06)

Riegel: T₂ = T₁ × (D₂/D₁)^n
- T₁ = 1h51m38s; D₁ = 17 km; D₂ = 21,1 km; n = 0,83
- Fator = (21,1/17)^0,83 ≈ 1,237
- **T₂ = ~2h18m57s**

**Faixas realistas:**
- **Best case** (taper executado, dia bom, sub-jejum carb-loading): **2h12-2h15**
- **Esperado** (plano cumprido normalmente): **2h17-2h21**
- **Worst case** (sem taper bom ou problema GI): **2h25+**

---

## 2. Periodização — 33 Dias até 06/06

**Estratégia:** Build curto (18 dias) + Taper (15 dias). Como TSB está +39, **NÃO há deload nesse plano** — você precisa de carga.

### 2.1. Visão geral semana a semana

| Semana | Datas | Foco | TSS-alvo | Longão | Pico CTL | TSB esperado |
|---|---|---|---|---|---|---|
| **1** | 04-10/mai | Build 1 — qualidade Z2 verdadeira + dose Z3 | ~280 | 18 km Z2 | 35 | +20 |
| **2** | 11-17/mai | Build 2 — adicionar limiar | ~320 | 19 km Z2 c/ progressão | 40 | +5 |
| **3** | 18-24/mai | Build 3 — pico de carga | ~340 | 20-21 km c/ 5 km ritmo prova | 44 | -5 a 0 |
| **4** | 25-31/mai | Taper início — volume cai 25-30% | ~240 | 16 km Z2 | 43 | +5 |
| **5** | 01-06/jun | Polish — volume cai 50-60% | ~150 | 10 km easy + toques | 41 | **+12 a +15** ✅ |

### 2.2. Distribuição de zonas no microciclo

- **Z1-Z2 (fácil):** 70% do volume (era 55-65%, mas você precisa REconstruir base aeróbia)
- **Z3 (limiar):** 15-20%
- **Z4-Z5 (qualidade):** 10-15%

### 2.3. Estrutura semanal típica (com força 3× já existente)

| Dia | Sessão Corrida (Build) | Força (1h) | Sessão Corrida (Taper) |
|---|---|---|---|
| Seg | Descanso de corrida | **Sessão A — MMII pesado** | Descanso de corrida + Força A reduzida |
| Ter | Intervalado Z4 (manhã) | — | Intervalado curto |
| Qua | Easy Z1-Z2 5-6 km (manhã) | **Sessão B — Upper + core** | Easy Z1 + Força B reduzida |
| Qui | Tempo run Z3 (5-7 km) | — | Tempo curto Z3 (3-4 km) |
| Sex | Descanso de corrida | **Sessão C — Funcional/unilateral** | Descanso + Força C reduzida |
| Sáb | Easy Z2 6-8 km | — | Easy Z2 5 km |
| Dom | **LONGÃO Z2** (122-132 bpm) | — | Longão reduzido |

**Regra do taper:** volume corrida cai rápido, intensidade cai devagar. Força mantém frequência mas corta 1 série e reduz carga em 30%. Sem pliometria nas semanas 4-5.

**Total semanal médio em Build:** ~38-45 km corrida + 3h força + core diário = carga total alta. **Vigie sinais de overreaching** (HRV baixo + sono ruim por 3 dias) — se acontecer, corte 1 sessão de força (não a corrida).

---

## 3. Modalidades de Recuperação

### 3.1. Pirâmide de Halson (NSCA Essentials of Sport Science 2021)

```
              ┌──────────────────────┐
              │ Terapias avançadas   │  ← último recurso
              ├──────────────────────┤
              │ Modalidades manuais  │  ← massagem, SMR, contraste
              ├──────────────────────┤
              │ Nutrição + Hidratação│  ← bloco diário
              ├──────────────────────┤
              │       SONO           │  ← BASE INEGOCIÁVEL
              └──────────────────────┘
```

### 3.2. Sono (prioridade #1)

- **Meta:** 7,5-9 horas/noite. Para 50+, regularidade > duração isolada.
- **Higiene:** quarto fresco, sem tela 1h antes, mesmo horário todos os dias inclusive sáb/dom.
- **Soneca:** 20-30 min, antes das 16h. Acima de 30 min ou após 16h prejudica sono noturno.
- **Atenção:** álcool fragmenta sono — corte 0 nas 4 noites pré-prova.
- **Métrica:** Garmin Sleep Score ≥ 80 = bom; < 70 = ajuste agendado de treino no dia seguinte.

### 3.3. Massagem (modalidade com mais evidência — UFMG, SciELO)

- **Frequência (build):** 1×/semana, 45-60 min, terapêutica/esportiva.
- **Frequência (taper):** 1× a cada 7-10 dias; massagem **leve** nos últimos 3 dias (não profunda).
- **Timing:** 12-24h após treino mais pesado (geralmente segunda-feira após longão de domingo).
- **Auto-massagem (todos os dias):** 5-10 min com bola/foam em panturrilhas, glúteos, planta do pé.

### 3.4. Foam Roller / SMR (Self-Myofascial Release)

Protocolo de 10-15 min, **3-5×/semana**:

| Região | Tempo | Notas |
|---|---|---|
| Panturrilha (gastroc + sóleo) | 60-90s/lado | Crítico para 50+ — risco de Aquiles |
| Quadríceps | 60-90s/lado | |
| Glúteo (max + médio + piriforme) | 60-90s/lado | Ataca dor lombar e síndrome IT band |
| Posterior de coxa | 60-90s/lado | |
| TFL/banda IT | 45-75s/lado | Cuidado: sensível, não forçar |
| Adicional: flexor de quadril (psoas) | 45-60s/lado | Importante para corredor sentado o dia |

**Intensidade:** desconforto tolerável (6-7/10), nunca dor aguda. Respiração solta.

### 3.5. Crioimersão (CWI) e Banho de Contraste — ⚠️ ATENÇÃO

**Evidência crítica:** Roberts et al. 2015 e Allan et al. 2022 mostram que **CWI rotineira pós-treino atenua adaptações** (síntese proteica, sinalização para hipertrofia/mitocôndria).

**Protocolo de uso:**

| Cenário | CWI? | Banho de contraste? |
|---|---|---|
| Build (semanas 1-3) | **NÃO** rotina. Só após treino excepcional ou se DOMS > 7/10 | OK 1-2×/sem (6 min: 1' frio @ 12°C : 2' quente @ 38°C × 2 ciclos) |
| Taper (semanas 4-5) | OK pontual após longão | OK 2×/sem |
| Pós-prova (06/06) | **SIM** — 10-15°C × 10-15 min logo após | OK |

**Resumo:** durante a fase de build, deixe seu corpo "doer um pouco" — é onde mora a adaptação. Reserve crioterapia para depois da prova.

### 3.6. Alongamento e mobilidade

- **Pós-treino:** 5-10 min de mobilidade ativa + alongamento leve (20-30s/posição).
- **Dia separado (1-2×/sem):** sessão de 20-30 min com PNF leve, foco em quadril, tornozelo, torácica.
- **Pré-treino:** mobilidade ativa (skipping, circundução, lunge dinâmico) — NUNCA alongamento estático longo (reduz potência por até 1h).

### 3.7. Compressão e recuperação ativa

- **Meias de compressão:** após longão, 2-4h. Evidência mista mas baixo custo + sensação de "perna leve".
- **Botas pneumáticas:** se acessível, 20-30 min após sessões pesadas.
- **Recuperação ativa:** caminhada 20-40 min ou bike Z1 no dia seguinte ao treino forte. Nunca substitui descanso total se for o caso.

### 3.8. Protocolo semanal exemplo (semana de Build)

| Dia | Manhã | Tarde/Noite | Modalidade |
|---|---|---|---|
| Seg | Sleep ≥ 8h | Massagem 45 min | DESCANSO TOTAL |
| Ter | Intervalado Z4 | Foam 10 min + sleep | — |
| Qua | Easy Z1 35 min | Mobilidade 20 min | Recuperação ativa |
| Qui | Tempo run Z3 | Foam 10 min | — |
| Sex | Força + core | Auto-massagem panturrilha | DESCANSO de corrida |
| Sáb | Easy Z2 + força | — | — |
| Dom | LONGÃO Z2 | Compressão 2h + foam | Mobilidade leve |

---

## 4. Nutrição e Suplementação para 98 kg

### 4.1. Necessidades diárias

**Calorias (Mifflin-St Jeor):**
- BMR = 10×98 + 6,25×190 - 5×54 + 5 = 980 + 1187,5 - 270 + 5 = **~1903 kcal/d**
- Manutenção (ativo, treino 4-5×/sem): BMR × 1,55 = **~2950 kcal/d**
- Em build: **2950 kcal/d** (manutenção). Não tente perder peso forte em 33 dias.

**Macros:**

| Macro | g/kg/d | g/d para 98 kg | kcal | % VCT |
|---|---|---|---|---|
| **Proteína** | 1,8 | **176** | 705 | 24% |
| **Carbo (build)** | 6 | **588** | 2350 | 80% (sobrepõe ajuste) |
| **Carbo (carb-load)** | 8-10 | 784-980 | 3140-3920 | — |
| **Gordura** | 0,8-1,0 | 80-100 | 720-900 | 24% |

**Distribuição:** 4 refeições + lanche pós-treino. Cada refeição com 0,4 g/kg de proteína (~40 g).

### 4.2. Janela pós-treino (30-60 min)

- **Proteína:** 0,3-0,4 g/kg = **30-40 g** (1 dose de whey 30g + iogurte/ovos)
- **Carbo:** 1,0-1,2 g/kg = **98-118 g** (banana grande + 80g aveia + mel ou pão + geleia + suco)
- **Proporção carbo:proteína:** 3:1 (suficiente). 4:1 só se houver outra sessão em < 8h.

**Exemplos práticos pós-treino:**

| Opção | Proteína | Carbo |
|---|---|---|
| Whey 40g + banana grande + 2 fatias pão + mel | 38 g | ~95 g |
| Iogurte grego 350g + 70g aveia + banana + mel | 35 g | ~110 g |
| Tapioca 80g + ovo 2 + queijo + suco laranja 300ml + banana | 28 g | ~115 g |

### 4.3. Hidratação (98 kg)

- **Base diária:** 35-40 ml/kg = **3,4-3,9 L/d**
- **Teste de sudorese:** pese-se nu antes/depois de 1h de treino, some bebida ingerida. Diferença = perda. (Provavelmente entre 0,8-1,5 L/h em SP).
- **Sódio em treino > 60 min:** 300-700 mg/h (você é homem com 98 kg, suor provavelmente alto — comece com 500 mg/h).
- **Hiponatremia:** evite beber muita água sem sódio em treinos > 90 min ou na prova.

### 4.4. Suplementação com evidência (ISSN position stands)

| Suplemento | Dose | Quando | Evidência |
|---|---|---|---|
| **Creatina monohidratada** | 5 g/d (sem fase de saturação) | Diariamente, qualquer hora | Forte para 50+: combate sarcopenia, melhora função neuromuscular. Endurance: ganho marginal mas significativo na fase final |
| **Whey protein** | 30-40 g/dose | Pós-treino + 1 dose extra se difícil bater 176 g/d | Forte |
| **Cafeína** | 3-6 mg/kg = 300-590 mg | 60 min antes de prova/treino-chave | Forte (Burke 2019). **Para 98 kg comece com 300-400 mg.** Teste em treino |
| **Ômega-3 (EPA+DHA)** | 1-2 g/d combinados | Diariamente, com refeição | Moderada — anti-inflamatório, recuperação |
| **Vitamina D3** | 1000-2000 UI/d | Diariamente | Para 50+ Brasil — peça exame 25(OH)D antes de dose alta |
| **Beta-alanina** | NÃO recomendado | — | Benefício marginal em 21K + saturação leva 4 semanas |
| **Bicarbonato** | NÃO | — | Não vale risco GI em 21K |

### 4.5. Carb-loading 48-72h pré-prova (04-05/06)

- **04/06 (sex):** 8 g/kg × 98 = **784 g de carbo** (distribuído em 5-6 refeições)
- **05/06 (sáb, dia anterior):** 8-10 g/kg = **784-980 g**, **reduzir fibras** (corte feijão, integrais, cruciferas, oleaginosas)
- **Evitar:** alimentos novos, gordura excessiva, álcool

**Café da manhã 06/06 (3h antes da prova):**
- 3 g/kg de carbo = **~290 g**
- Exemplo: 100g aveia + banana 2× + mel 30g + iogurte natural 200g + pão 4 fatias com geleia + suco laranja 300ml
- **Líquido importante:** café (cafeína 300 mg total), 500 ml de água com pouco sal

### 4.6. Estratégia intra-prova 21K (~2h18)

- **Consumo:** 60 g de carbo/h via gel ou bebida
- **Plano:** gel a cada 35-40 min começando km 5
  - km 5: gel 1 (~25 g carbo)
  - km 10: gel 2 + água com isotônico
  - km 14-15: gel 3
  - km 18-19: opcional gel 4 ou só hidratação
- **Hidratação:** 150-250 ml a cada estação (5 km)
- **Sódio:** isotônico nos pontos pares + sal opcional na palma
- **REGRA DE OURO:** **NADA NOVO NO DIA**. Teste todos os géis nos longões pré-prova.

### 4.7. Cardápio diário tipo (2950 kcal, 176g P, 588g C)

| Refeição | Alimentos | P | C |
|---|---|---|---|
| Café (7h) | Aveia 80g + leite 300ml + banana + ovos 3 + 2 fatias pão integral + queijo branco 40g | 40 | 100 |
| Lanche (10h) | Iogurte natural 200g + granola 40g + mel | 12 | 50 |
| Almoço (12h30) | Arroz 250g cozido + feijão 150g + frango 200g + salada + azeite 1 cs | 50 | 130 |
| Pós-treino (16h)* | Whey 30g + banana + pão 2 fatias + mel | 33 | 95 |
| Jantar (19h30) | Batata-doce 350g + peixe 200g + legumes + azeite | 45 | 75 |
| Ceia (21h30) | Iogurte + chia 1 cs | 8 | 15 |
| **Total** | | **~188** | **~465** |

*Em dias sem treino, pular o pós-treino e ajustar almoço/jantar.

---

## 5. Treinamento Complementar

### 5.1. Força (3×/semana — você já faz seg/qua/sex 1h cada; mantém)

**Princípio:** organizar as 3 sessões para que MMII pesado não preceda treino-chave de corrida (intervalado terça, tempo quinta, longão domingo). Sem histórico de lesão = sinal verde para progressão de carga mais ousada.

**Em taper (sem 4-5):** mantém frequência 3×, mas corta 1 série de cada exercício e reduz cargas em 30%. Sem pliometria nas 2 últimas semanas.

#### Sessão A — Segunda (Full body / MMII pesado)

| Exercício | Séries × Reps | Notas |
|---|---|---|
| Agachamento (livre ou goblet) | 4 × 6-8 | Carga próxima da falha técnica |
| Levantamento terra romeno (RDL) | 3 × 8-10 | Posterior coxa + glúteo |
| Hip thrust (elevação pélvica) | 3 × 10 | Glúteo máx — propulsão |
| Panturrilha unilateral | 3 × 12-15/lado | **CRÍTICO** — prevenção Aquiles |
| Core: prancha + dead bug | 3 × 45s + 10/lado | Estabilização |

> **Por que segunda:** você teve domingo de longão. Segunda já está parcialmente recuperado, e há 5 dias até o próximo longão. Distância máxima.

#### Sessão B — Quarta (Upper + core estabilidade)

| Exercício | Séries × Reps | Notas |
|---|---|---|
| Remada (curvada ou pulley) | 4 × 8-10 | Postura |
| Supino (livre ou máquina) | 3 × 8-10 | Equilíbrio postural |
| Tração (assistida se preciso) ou pull-down | 3 × 8-10 | Latíssimo, postura |
| Desenvolvimento de ombro | 3 × 10 | Estabilidade braço/cabeça |
| Core: prancha lateral + paloff press | 3 × 30s/lado + 10/lado | Anti-rotação |
| Mobilidade torácica + quadril | 10 min | Bloco final |

> **Por que upper na quarta:** terça você fez intervalado, quinta vai fazer tempo run. Pernas precisam estar frescas. Esta sessão preserva estímulo de força sem interferir.

#### Sessão C — Sexta (Funcional / unilateral)

| Exercício | Séries × Reps | Notas |
|---|---|---|
| Split squat (afundo unilateral) | 3 × 8/perna | Estabilidade unilateral — chave 50+ |
| Single-leg deadlift | 3 × 8/perna | Equilíbrio + cadeia posterior |
| Ponte unilateral de glúteo | 3 × 10/lado | Glúteo médio (anti-IT band) |
| Panturrilha unilateral (variação 2) | 3 × 12-15/lado | Sentado para sóleo |
| Core: bird dog + paloff | 3 × 10/lado | Coordenação |
| **Pliometria leve** (sem 1-3 apenas) | Pular corda 3×1min ou skipping | Cortar nas sem 4-5 |

> **Por que funcional na sexta:** 36h até o longão de domingo. Carga moderada, foco em padrões unilaterais que melhoram economia de corrida sem deixar perna pesada.

### 5.2. Core (2-3×/semana, 15-20 min)

| Exercício | Tempo/Reps |
|---|---|
| Prancha frontal | 3 × 45-60s |
| Prancha lateral | 3 × 30-45s/lado |
| Dead bug | 3 × 10/lado |
| Bird dog | 3 × 10/lado |
| Single-leg deadlift (sem peso ou leve) | 3 × 8/perna |
| Paloff press com elástico | 3 × 10/lado |

### 5.3. Pliometria (versão segura para 98 kg)

- **Apenas semanas 1-3** (corte na semana 4 e 5)
- **1× por semana**, 10 min, BAIXO impacto:
  - Pular corda 3 × 1 min (intervalo 1 min)
  - Skipping leve 3 × 30s
  - Saltos baixos com amortecimento controlado 2 × 6
- **Critério para fazer:** sem dor em panturrilha/Aquiles na semana

### 5.4. Mobilidade (todos os dias, 5-10 min)

- Tornozelo: dorsiflexão na parede 2 × 10/lado
- Quadril: 90/90 hip flow 2 × 5/lado
- Torácica: thread the needle, cat-cow 1 × 8

### 5.5. Prevenção de lesão para 98 kg / 54 anos

**Lesões com prevalência alta nessa faixa:**
- Tendinite de Aquiles → panturrilha unilateral é PROFILAXIA
- Fascite plantar → mobilidade pé, rolar bola, tolerância progressiva
- IT band syndrome → fortalecer glúteo médio (afundo, ponte unilateral)
- Estresse tibial medial (canelite) → não aumentar volume > 10%/semana

**Sinais de alerta:**
- Dor que persiste > 48h após treino
- Dor que muda padrão de passada (compensação)
- Inchaço local
→ **Pare e procure fisio. NÃO empurre — você não tem 33 dias para tratar uma lesão.**

---

## 6. Monitoramento — HRV e PMC

### 6.1. Garmin HRV Status (4 níveis)

A Garmin (parceria com Firstbeat) compara sua HRV noturna com **sua baseline pessoal** construída em **mínimo 19 dias** de uso 24/7.

| Status | Interpretação | Ação no protocolo |
|---|---|---|
| **Balanced** (verde) | Dentro da faixa pessoal | Treino conforme planejado |
| **Unbalanced** (laranja) | Fora da faixa (alta OU baixa) | Reduzir intensidade do dia em 1 nível |
| **Low** (vermelho) | Abaixo da faixa por dias | Treino fácil ou descanso |
| **Poor** | Muito abaixo + tendência | DESCANSO. Revisar sono/estresse |

**Métrica que Garmin usa:** RMSSD durante o sono (a janela de 4-8h da noite).
**Tempo para baseline confiável:** ~3 semanas de uso 24/7.

### 6.2. Score composto diário (sua regra de decisão)

```
Score = HRV(0,25) + BodyBattery(0,25) + Sleep(0,20) + 
        Readiness(0,15) + TSB_trend(0,05) + CTL_trend(0,10)
```

| Score | Decisão | Detalhamento |
|---|---|---|
| ≥ 0,90 | TREINAR FORTE | Executa tudo conforme planilha |
| 0,60-0,89 | MODERADO | Reduz intensidade em 1 zona; mantém volume |
| 0,30-0,59 | FÁCIL | Só Z1-Z2, volume -30% |
| < 0,30 | DESCANSO TOTAL | Mobilidade + sono |

**Outliers a vigiar:**
- HRV cai > 1 desvio-padrão em 1 noite → atenção (estresse pontual)
- HRV cai por 3 noites seguidas → PARE e investigue (pré-overreaching)
- FC repouso sobe > 5 bpm vs baseline → mesmo sinal

### 6.3. Sinais de overreaching (não funcional)

Se você notar **3 ou mais simultaneamente**:
- HRV abaixo da baseline por > 4 dias
- FC repouso elevada
- Sono pior (mesmo deitando bem)
- Performance cai (mesmo pace, FC mais alta)
- Irritabilidade, perda de motivação
- Soreness persistente

**Ação:** corte 1 semana para 50% do volume, sem qualidade. Avalie de novo na semana seguinte.

---

## 7. Sistema Técnico Python — Pipeline Garmin/TrainingPeaks

### 7.1. Arquitetura recomendada

```
┌─────────────────────┐         ┌──────────────────────┐
│  Garmin Connect     │         │  TrainingPeaks Prem  │
│  (web/app)          │         │                      │
└──────┬──────────────┘         └────────────┬─────────┘
       │ garth (lib Python)                  │ Export CSV
       │ (HRV, sleep, body battery, status)  │ (TSS, IF, dist, dur)
       ▼                                     ▼
┌──────────────────────────────────────────────────────┐
│             collector.py (cron 06:00)                 │
│  - autentica garth (e-mail + senha + OAuth token)    │
│  - busca métricas dos últimos 7 dias                 │
│  - lê CSV TP (mais recente em ./inbox)               │
│  - salva em SQLite                                    │
└──────────┬───────────────────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────────┐
│             scoring.py                                │
│  - calcula score composto + classifica dia           │
│  - reconstrói PMC (CTL/ATL/TSB) se TP não exportar   │
│  - detecta outliers (HRV drop, RHR sobe)             │
└──────────┬───────────────────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────────┐
│        notify.py (e-mail + Telegram)                  │
│        dashboard.py (Streamlit local)                 │
└──────────────────────────────────────────────────────┘
```

### 7.2. Stack

```bash
pip install garth pandas numpy plotly streamlit python-dotenv \
            apscheduler python-telegram-bot duckdb
```

**Bibliotecas-chave:**
- **garth** ([github.com/matin/garth](https://github.com/matin/garth)) — extrai HRV diário, sleep, body battery, training readiness do Garmin Connect via login pessoal (não precisa Health API empresarial)
- **python-garminconnect** ([github.com/cyberjunky/python-garminconnect](https://github.com/cyberjunky/python-garminconnect)) — alternativa mais ampla
- **pandas** — manipulação CSV TP
- **DuckDB** ou **SQLite** — storage local privado
- **Streamlit** — dashboard 1 página

### 7.3. Schema banco (SQLite)

```sql
CREATE TABLE daily_metrics (
  date DATE PRIMARY KEY,
  hrv_overnight INTEGER,        -- RMSSD ms
  hrv_status TEXT,              -- 'BALANCED', 'UNBALANCED', 'LOW', 'POOR'
  body_battery_morning INTEGER, -- 0-100
  body_battery_min INTEGER,
  sleep_score INTEGER,
  sleep_duration_hours REAL,
  resting_hr INTEGER,
  training_readiness INTEGER,   -- 0-100
  training_status TEXT,
  weight_kg REAL
);

CREATE TABLE activities (
  activity_id TEXT PRIMARY KEY,
  date DATE,
  type TEXT,
  distance_km REAL,
  duration_min REAL,
  hr_avg INTEGER,
  pace_min_per_km REAL,
  tss REAL,
  if_value REAL
);

CREATE TABLE pmc (
  date DATE PRIMARY KEY,
  ctl REAL,
  atl REAL,
  tsb REAL
);

CREATE TABLE decisions (
  date DATE PRIMARY KEY,
  score REAL,
  classification TEXT,           -- 'STRONG', 'MODERATE', 'EASY', 'REST'
  notes TEXT,
  planned_session TEXT,
  actual_session TEXT
);
```

### 7.4. Reconstrução do PMC se TP não exportar CTL/ATL/TSB

Fórmulas exponenciais (Coggan):

```python
import pandas as pd
import numpy as np

def calculate_pmc(df_tss, ctl_decay=42, atl_decay=7, ctl_init=31, atl_init=14):
    """df_tss: DataFrame com colunas ['date', 'tss']"""
    df_tss = df_tss.sort_values('date').reset_index(drop=True)
    ctl, atl = [ctl_init], [atl_init]
    for i in range(len(df_tss)):
        tss = df_tss.loc[i, 'tss'] or 0
        new_ctl = ctl[-1] + (tss - ctl[-1]) * (1 - np.exp(-1/ctl_decay))
        new_atl = atl[-1] + (tss - atl[-1]) * (1 - np.exp(-1/atl_decay))
        ctl.append(new_ctl)
        atl.append(new_atl)
    df_tss['ctl'] = ctl[1:]
    df_tss['atl'] = atl[1:]
    df_tss['tsb'] = df_tss['ctl'] - df_tss['atl']
    return df_tss
```

### 7.5. Lógica de decisão (scoring.py)

```python
def normalize(value, low, high):
    if value is None: return 0.5
    return max(0, min(1, (value - low) / (high - low)))

def hrv_status_score(status):
    return {'HIGH': 1.0, 'BALANCED': 0.85, 'UNBALANCED': 0.4, 'LOW': 0.2, 'POOR': 0.0}.get(status, 0.5)

def calculate_daily_score(metrics):
    score = (
        0.25 * hrv_status_score(metrics['hrv_status']) +
        0.25 * normalize(metrics['body_battery_morning'], 30, 90) +
        0.20 * normalize(metrics['sleep_score'], 60, 90) +
        0.15 * normalize(metrics['training_readiness'], 30, 90) +
        0.05 * (1 if metrics['tsb'] > -15 else max(0, (metrics['tsb']+30)/15)) +
        0.10 * normalize(metrics['ctl_trend_7d'], -2, 2)
    )
    return score

def classify_day(score, tsb):
    if score >= 0.90 and tsb > -10:
        return 'STRONG'
    elif score >= 0.60:
        return 'MODERATE'
    elif score >= 0.30:
        return 'EASY'
    else:
        return 'REST'
```

### 7.6. Esqueleto coletor (collector.py)

```python
import garth
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

def get_garmin_data(days=7):
    garth.login(os.getenv('GARMIN_EMAIL'), os.getenv('GARMIN_PASSWORD'))
    garth.save('~/.garth')  # cacheia OAuth token
    end = datetime.now().date()
    start = end - timedelta(days=days)
    
    hrv_data = garth.DailyHRV.list(start, days)
    sleep_data = garth.DailySleep.list(start, days)
    body_battery = garth.DailyBodyBattery.list(start, days)
    
    return {'hrv': hrv_data, 'sleep': sleep_data, 'bb': body_battery}

def parse_tp_export(csv_path):
    import pandas as pd
    df = pd.read_csv(csv_path)
    df['Date'] = pd.to_datetime(df['Date'])
    return df[['Date', 'TSS', 'IFactor', 'Distance', 'Duration', 'HRAverage']]
```

### 7.7. Schedule e notificações

**Cron diário (Linux/Mac):**
```bash
0 6 * * * /usr/bin/python3 /home/user/runtech/main.py >> /var/log/runtech.log 2>&1
```

**Windows Task Scheduler:** rodar `python.exe main.py` às 06:00.

**Telegram bot** (notificação curta):
```python
import telegram
bot = telegram.Bot(token=os.getenv('TG_TOKEN'))
bot.send_message(chat_id=os.getenv('TG_CHAT_ID'), 
                 text=f"⚡ {today}: {classification}\nTSB: {tsb:.0f} | HRV: {hrv_status}\nSugestão: {planned}")
```

### 7.8. Privacidade

- Credenciais em `.env` (NUNCA no código)
- Storage **local apenas** (SQLite)
- Não suba para GitHub público
- Use `keyring` (Python lib) em vez de .env se quiser camada extra
- Backup mensal cifrado (ex: `gpg -c`)

### 7.9. Repositórios de referência

- [github.com/matin/garth](https://github.com/matin/garth)
- [github.com/cyberjunky/python-garminconnect](https://github.com/cyberjunky/python-garminconnect)
- [github.com/topics/garmin-connect](https://github.com/topics/garmin-connect) — projetos similares
- Tutorial PMC: [reddit r/NorwegianSinglesRun TSS/CTL/ATL/TSB](https://www.reddit.com/r/NorwegianSinglesRun/comments/1odp9ig/)

---

## 8. Cronograma Concreto Semana a Semana

### Semana 1 — 04 a 10 de maio (Build 1 — corrigir base aeróbia)

| Dia | Corrida | Força | Modalidades |
|---|---|---|---|
| Dom 04/05 | DIAGNÓSTICO | — | Inicia tracking garth; medir FC repouso 3 manhãs |
| Seg 05/05 | Descanso de corrida | **Sessão A — MMII pesado** (1h) | Massagem opcional 45 min à noite |
| Ter 06/05 | Intervalado: 6×800m @ 5:30-5:45 c/ 90s descanso (após aquec 2km) | — | Foam 10 min |
| Qua 07/05 | Easy 5 km Z1-Z2 (115-128 bpm) | **Sessão B — Upper + core** (1h) | Mobilidade 10 min |
| Qui 08/05 | Tempo run: 2km aq + 5km @ Z3 (134-146) + 1km solto | — | Foam 10 min |
| Sex 09/05 | Descanso de corrida | **Sessão C — Funcional + pliometria leve** (1h) | — |
| Sáb 10/05 | Easy 8 km Z2 (122-132 bpm) | — | — |
| **Dom 11/05** | **LONGÃO 18 km @ Z2 verdadeiro (125-132 bpm)** — pace cair se preciso para 7:00-7:15 | — | Compressão pós, foam |

**Volume:** ~38 km corrida + 3h força. **TSS estimado:** ~280. **Meta CTL fim de sem:** 35-36.

### Semana 2 — 11 a 17 de maio (Build 2 — adicionar limiar)

| Dia | Corrida | Força |
|---|---|---|
| Seg 12 | Descanso de corrida | **Sessão A** (1h) — manter cargas |
| Ter 13 | Intervalado: 5×1km @ 5:25-5:35 c/ 2min | — |
| Qua 14 | Easy 6 km Z1-Z2 | **Sessão B** (1h) |
| Qui 15 | Tempo run: 2km aq + 7km @ Z3 + 1km solto | — |
| Sex 16 | Descanso de corrida | **Sessão C** (1h) com pliometria leve |
| Sáb 17 | Easy 8 km Z2 | — |
| Dom 18 | **LONGÃO 19 km Z2 com últimos 3 km em ritmo de prova (~6:30)** | — |

**Volume:** ~42 km corrida + 3h força. **TSS:** ~320. **Meta CTL:** 39-40.

### Semana 3 — 18 a 24 de maio (Build 3 — pico de carga)

| Dia | Corrida | Força |
|---|---|---|
| Seg 19 | Descanso de corrida | **Sessão A** (1h) — pico de carga |
| Ter 20 | Intervalado VO2: 6×3min @ Z4-Z5 c/ 2min trote | — |
| Qua 21 | Easy 6-7 km Z1-Z2 | **Sessão B** (1h) |
| Qui 22 | Tempo + ritmo: 2km aq + 4km Z3 + 4km ritmo prova + 1km solto | — |
| Sex 23 | Descanso de corrida | **Sessão C — reduz carga em 15%** (1h) |
| Sáb 24 | Easy 6 km Z2 | — |
| Dom 25 | **LONGÃO ESPECÍFICO 20-21 km com 5 km finais em ritmo de prova (~6:25-6:30)** | — |

**Volume:** ~45 km corrida + 3h força. **TSS:** ~340. **Meta CTL:** 43-44 (pico!). **TSB pode ir a -5 a 0** — normal.

### Semana 4 — 25 a 31 de maio (Taper Início)

| Dia | Corrida | Força |
|---|---|---|
| Seg 26 | Descanso de corrida | **Sessão A — TAPER** (carga -30%, 1 série a menos) |
| Ter 27 | Intervalado curto: 5×800m @ 5:25 (mantém intensidade) | — |
| Qua 28 | Easy 5 km Z1-Z2 | **Sessão B — TAPER** (cargas -30%) |
| Qui 29 | Tempo curto: 2km aq + 4km Z3 | — |
| Sex 30 | Descanso de corrida | **Sessão C — TAPER** (sem pliometria, cargas -30%) |
| Sáb 31 | Easy 5 km Z2 | — |
| Dom 01/06 | **LONGÃO REDUZIDO 15-16 km Z2** | — |

**Volume:** ~33 km corrida (-25%) + 3h força reduzida. **TSS:** ~240. **TSB sobe para +5.**

### Semana 5 — 01 a 06 de junho (Polish + PROVA)

| Dia | Corrida | Força | Hidratação/Nutrição |
|---|---|---|---|
| Seg 02/06 | Easy 4 km Z1-Z2 | **Sessão A — POLISH** (50% carga, 2 séries) | Início subindo carbo |
| Ter 03/06 | Toque qualidade: 2km aq + 3×400m @ ritmo prova + 1km solto | — | — |
| Qua 04/06 | Easy 4-5 km Z1 + drills | **Sessão B — POLISH** (apenas core leve, sem cargas pesadas) | **Carb-loading ativo (8 g/kg)** |
| Qui 05/06 | "Shake-out" 3-4 km muito leves + 4×100m strides | — | **Carb-load + corte fibras** |
| **Sex 06/06** | **PROVA 21K!** | — | Café 3h antes (3 g/kg carbo + cafeína 300mg) |

**TSB no dia da prova: +12 a +15** ✅
**Nota:** sexta de prova substitui sessão de força. Volta com força 3× normalmente após ~7 dias de recuperação.

### Plano da prova (06/06) — estratégia "90%, não PR"

- **3h antes:** café-da-manhã prescrito (290g carbo)
- **1h antes:** 200ml água + 200mg cafeína (parte da dose)
- **20 min antes:** aquecimento 10 min Z1 + 4×60m stride
- **Largada km 0-3:** **EM RITMO TÁTICO CONTROLADO** — pace 6:35-6:40 (NUNCA mais rápido que 6:30)
- **Km 3-18:** **pace alvo 6:30-6:35 estável** (não 6:25 como seria em modo PR)
- **Km 5, 10, 15:** géis (25g cada)
- **Km 18-21:** se houver gás sobrando, mantém 6:30 (NÃO acelere). Se estiver pesado, aceita 6:40-6:45 e termina inteiro
- **Hidratação:** 150-200 ml a cada estação, isotônico nas pares
- **Mentalidade:** "este é meu primeiro race-rehearsal — terminar com gasolina sobrando vale mais que cravar PR aqui". O PR de 21K vem em 26/07.

---

## 9. Recomendação Final e Riscos

### Pontos de atenção (em ordem de criticidade)

1. **🔴 LONGÃO EM Z2 VERDADEIRO (125-132 bpm)** — sua maior alavanca. Você está fazendo Z3 médio achando que é Z2. Cair para 125-130 bpm vai parecer "lento" — é.
2. **🔴 NÃO TENTE PERDER PESO AGRESSIVO** — 33 dias é curto. Manutenção + carbo na quantidade certa. Perda de peso vem depois da prova.
3. **🔴 CARGA TOTAL ALTA (corrida + 3h força)** — vigie HRV e sono. Se 3 dias seguidos com HRV baixo, corte 1 sessão de força (não a corrida-chave). Sem histórico de lesão é vantagem mas não dá imunidade.
4. **🟡 Se HRV cair 3 dias seguidos:** corte intensidade. Chegar saudável vale mais que pico de fitness.
5. **🟡 CWI/banho gelado:** evite na fase de build. Use só após a prova.
6. **🟡 Pliometria:** corte na sem 4 e 5. Risco/benefício ruim para 98 kg em taper.
7. **🟢 Massagem:** maior modalidade com evidência. 1×/semana, sempre.
8. **🟢 Sono:** se algum dia tiver < 7h, automático: treino seguinte é fácil ou descanso.
9. **🟢 FCrep 51 + sem histórico de lesão:** sinais ótimos. Sua base permite progressão um pouco mais ousada do que o padrão para amador 50+.

### O que fazer JÁ esta semana

1. **Hoje (04/05):** sincronizar Garmin com TrainingPeaks; verificar TSB exato; medir FC repouso 3 manhãs seguidas
2. **Esta semana:** comprar gel/isotônico que vai usar na prova; testar TODOS no longão de 11/05
3. **Esta semana:** começar suplementação (creatina 5g/d + ômega-3 1-2g/d + vit D 2000 UI); manter por 30 dias contínuos
4. **Próxima semana:** começar coleta com `garth`; depois de 14 dias você terá baseline para o sistema técnico
5. **Sexta 09/05:** primeira sessão de força com cargas leves (testar tolerância)

### Métricas para validar progresso a cada 7 dias

| Métrica | Sem 1 | Sem 2 | Sem 3 | Sem 4 | Sem 5 |
|---|---|---|---|---|---|
| CTL alvo | 35 | 40 | 44 | 43 | 41 |
| TSB alvo | +20 | +5 | -3 | +5 | +12 |
| Longão (km) | 18 | 19 | 20-21 | 15-16 | — |
| HRV Status médio | balanced | balanced | unbalanced OK 1-2 dias | balanced | balanced/high |
| Peso | 98 | 97-98 | 97-98 | 96-97 | 96-97 |

### Confiança e ressalvas

- **Periodização:** alta confiança (consenso entre Friel/Daniels/Magness para meia-maratona em janela curta)
- **Projeção 21K:** Riegel é modelo simples; o real depende de execução do taper, dia da prova, clima
- **Doses de suplementos:** baseadas em ISSN position stands, mas verifique com seu médico/nutri se houver comorbidade
- **Sistema técnico:** funciona, mas garth/python-garminconnect podem quebrar se Garmin mudar algo no Connect — tenha plano B (export manual)
- **Limite biológico:** aos 54 anos com IMC 27,1, espere ganhos de fitness mais lentos. Foque em chegar inteiro mais que em "voar"

### Próximo passo recomendado

Compartilhe seu **maior longão simulado em Z2 verdadeiro (125-132 bpm)** após executar a primeira semana — esse será o melhor preditor da projeção 21K final. Anote pace médio, FC média e percepção de esforço.

---

## Fontes e Catálogo

Detalhes em `fontes.md` (catálogo legível) e `fontes.json` (estruturado, máquina).
**~50 fontes catalogadas** — distribuição: 17 Tier A | 22 Tier B | 8 Tier C | 3 Tier D.

---

*Relatório gerado por /pesquisa_v2 em 2026-05-04. Atualize quando houver mudança em peso, FCrep, ou ocorrer lesão.*
