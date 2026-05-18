"""dash_glossary.py - Glossario de termos tecnicos do dashboard.

Cada termo tem:
  - id: usado pra ancora HTML (glossario-{id})
  - title: titulo principal exibido
  - aliases: lista de outros nomes pelo qual aparece nos cards (BB MAX, BODY BATTERY MAX, etc)
  - category: badge de categoria
  - color: cor associada (combina com a metrica no dashboard)
  - body_md: conteudo em markdown que sera renderizado pra HTML

Pra adicionar novos termos: append GLOSSARY com novo dict.
"""

GLOSSARY = [
    {
        "id": "hrv",
        "title": "HRV Overnight",
        "aliases": ["HRV", "HRV — ÚLTIMA NOITE", "HRV OVERNIGHT"],
        "category": "Indicador autonômico",
        "color": "#ff3b30",
        "body_md": """
**HRV (Heart Rate Variability)** = a variação dos intervalos entre batimentos cardíacos. Cada batimento não é metronômico — entre um e outro existem microvariações de milissegundos. HRV é o desvio-padrão dessas variações.

O Garmin mede durante o sono ("overnight") porque é o sinal mais limpo do dia: sem ruído de movimento, café, estresse mental ou comida.

### O que significa

- **HRV alta** → sistema parassimpático dominando → corpo recuperado, pronto pra absorver carga
- **HRV baixa** → sistema simpático dominando → corpo em modo de defesa, ainda processando estresse

### O que influencia (em ordem de impacto)

| Fator | Efeito | Latência |
|---|---|---|
| Álcool | −20 a −40% | mesma noite |
| Treino intenso (Z4-Z5) | −10 a −25% | 24-48h |
| Doença incipiente | −15 a −30% | **24-48h ANTES dos sintomas** |
| Sono curto (<6h) ou ruim | −10 a −20% | imediato |
| Refeição pesada perto de dormir | −5 a −15% | mesma noite |
| Cafeína após 14h | −5 a −10% | mesma noite |
| Desidratação | −5 a −15% | mesma noite |
| Estresse mental forte | −5 a −20% | mesma noite |
| Sono profundo (REM + Deep altos) | +5 a +15% | imediato |
| Z2 bem dosado | neutro / levemente positivo | — |

### Faixas pra atletas amadores 50+

- **Saudável típico:** 25-50 ms
- **Alvo deste dashboard:** ≥32 ms
- **Crítico (precaução):** <26 ms (gate vermelho)

### Como subir

Alavancas grandes: dormir 8h+ com REM ≥70 min · cortar álcool · última refeição 3h antes de deitar.
Alavancas médias: hidratação contínua · respiração 4-7-8 antes de dormir · cafeína cortada após 14h.
""",
    },
    {
        "id": "body-battery",
        "title": "Body Battery (BB)",
        "aliases": ["BB", "BB MAX", "BODY BATTERY", "BODY BATTERY MAX"],
        "category": "Reserva de energia",
        "color": "#bf5af2",
        "body_md": """
**Body Battery (BB)** é uma estimativa proprietária do Garmin que combina HRV, FCrep, qualidade de sono e atividade física pra estimar o quanto de "bateria" o corpo tem disponível, numa escala 0-100.

### Como ler

- **0-25:** baixíssima — corpo precisa de descanso real
- **25-50:** baixa — opere em volume reduzido
- **50-70:** moderada — treino normal OK
- **70-100:** alta — pronto pra carga maior

### O que sobe

- Sono de qualidade (especialmente REM + Deep)
- Períodos de relaxamento (HRV alta durante o dia)
- Refeição balanceada
- Hidratação

### O que desce

- Atividade física (proporcional à intensidade — Z5 derruba ~25 pts em 24h)
- Estresse mental medido (Garmin estima via HRV diurno)
- Refeições pesadas (digestão consome bateria)
- Sono ruim
- Álcool

### Métricas mostradas no dashboard

- **BB MAX:** o pico que você atingiu nas últimas 24h. Geralmente atingido logo após acordar.
- **BB MIN:** o vale. Geralmente próximo da hora de dormir.
- **Carga / Desgaste:** quanto subiu e quanto baixou no dia.

### Alvo prático

Pra um treino "normal", quero acordar com **BB MAX ≥65**. Pra longão ou intervalos pesados, **≥75**. Abaixo de 50 = sinal pra reduzir carga ou descansar.
""",
    },
    {
        "id": "fcrep",
        "title": "FC Repouso (FCrep)",
        "aliases": ["FCREP", "FC REPOUSO", "FC REP", "RESTING HEART RATE"],
        "category": "Indicador cardiovascular",
        "color": "#30d158",
        "body_md": """
**FC Repouso (FCrep)** = frequência cardíaca em repouso, medida pelo Garmin durante períodos de baixa atividade (geralmente nos primeiros minutos após acordar ou em momentos de inatividade prolongada durante o dia).

### Por que importa

A FCrep é uma janela direta pro **estado autonômico crônico**. Diferente da HRV (que oscila bastante dia a dia), a FCrep é mais estável — variações de 2-3 bpm são significativas.

### Como ler (relativo ao SEU baseline)

- **No baseline ou abaixo:** corpo recuperado, treino tolerável
- **+2 a +4 bpm vs baseline:** sinal de fadiga acumulada ou estresse incipiente
- **+5 ou mais:** **sinal forte** — pode ser overtraining, doença chegando, dívida de sono, ou desidratação

### O baseline pro este dashboard

**51 bpm** — calibrado a partir do seu histórico Garmin. O alvo é manter ≤53 bpm na manhã.

### O que sobe a FCrep (sem ser benéfico)

- Doença chegando (frequentemente sobe 3-5 bpm 24-48h ANTES dos sintomas)
- Desidratação
- Fadiga acumulada
- Álcool na noite anterior
- Refeição muito perto de dormir
- Estresse psicológico crônico
- Calor / quarto quente

### O que desce a FCrep (saudável)

- Adaptação aeróbica progressiva (1-3 bpm ao longo de meses de Z2 disciplinado)
- Sono regular e profundo
- Hidratação adequada
- Resolução de inflamação

### Sinal de alerta

Se FCrep ficar ≥56 bpm por **2+ dias seguidos** sem causa óbvia (treino pesado recente), considerar: pode ser doença subclínica. Recuar volume + observar.
""",
    },
    {
        "id": "disposicao",
        "title": "Disposição (Garmin Readiness)",
        "aliases": ["READINESS", "DISPOSIÇÃO", "DISPOSICAO", "TRAINING READINESS"],
        "category": "Score composto Garmin",
        "color": "#ff9500",
        "body_md": """
**Training Readiness** é o score 0-100 do Garmin que tenta resumir num número só "como seu corpo está pra treinar hoje". Combina:

- HRV overnight
- Qualidade do sono (duração, fases)
- Recovery time pendente do último treino
- Estresse acumulado
- Body Battery atual

### Como ler

- **0-25:** baixa — descanso recomendado
- **25-50:** moderada — treino leve OK
- **50-75:** boa — treino normal
- **75-100:** alta — pronto pra carga ou intensidade

### Por que NÃO é a métrica-chefe

Por ser composto e proprietário, **Readiness pode mascarar sinais discordantes**. Exemplo real seu: dia 09/05 mostrou 76 (alto), mas HRV estava 31 (1 abaixo do alvo). O score Garmin se baseou no sono bom + tempo desde último treino, ignorando que o autonômico ainda não estava 100%.

**Regra prática:** quando Readiness e HRV/FCrep discordam, **prefira HRV+FCrep como verdade**. Readiness é confirmatório, não decisivo.

### Quando Readiness é útil

- Como sanity check rápido nos dias em que você está com pressa
- Pra ver tendência ao longo da semana (se média sobe/desce)
- Pra explicar o porquê de uma queda (Garmin lista os fatores que pesaram)
""",
    },
    {
        "id": "sono",
        "title": "Sono / Sleep Score",
        "aliases": ["SLEEP", "SLEEP SCORE", "SONO", "SONO TOTAL"],
        "category": "Recuperação fisiológica",
        "color": "#0a84ff",
        "body_md": """
**Sleep Score** é o score Garmin (0-100) que avalia a qualidade do sono combinando duração total, distribuição entre fases (REM/Deep/Light/Awake) e respostas autonômicas durante o sono.

### Faixas

- **<60:** ruim — sono insuficiente ou fragmentado
- **60-74:** moderado — funcional mas sem otimização
- **75-89:** bom — atende necessidades básicas
- **≥90:** excelente — recuperação ótima

### Fases do sono — o que cada uma faz

| Fase | % típico | Função |
|---|---|---|
| **REM** | 20-25% | Consolidação de memória, aprendizado motor, regulação emocional |
| **Deep (N3)** | 15-20% | Recuperação física, hormônio do crescimento, reparação muscular, imunidade |
| **Light (N1+N2)** | 50-60% | Maior fatia, transição entre fases |
| **Awake** | <5% | Despertares breves — quanto menos, melhor |

### Alvos pra atletas

- **Total:** ≥8h (480 min) — atletas amadores em fase de carga precisam mais que pessoa sedentária
- **REM:** ≥70 min (≥1h10) — crítico pra adaptação de aprendizado motor e recuperação cognitiva
- **Deep:** ≥60 min (≥1h00) — onde a recuperação muscular acontece de verdade
- **Awake:** <30 min — fragmentação > 30 min indica sono ruim

### O que sabota o sono

- Cafeína após 14h
- Álcool (derruba REM violentamente — você dorme, mas não recupera)
- Tela com luz azul até a hora de deitar
- Quarto quente (>21°C)
- Treino intenso < 3h antes de dormir
- Refeição pesada < 2h antes de dormir
- Estresse mental não-processado

### O que ajuda

- Mesma hora de deitar e acordar (regularidade > duração)
- Quarto frio (18-19°C) e escuro
- Exposição ao sol pela manhã (regula melatonina à noite)
- 30-45 min sem tela antes de deitar
- Respiração 4-7-8 ao deitar
""",
    },
    {
        "id": "training-status",
        "title": "Training Status",
        "aliases": ["TRAINING STATUS", "VO2 MAX TREND"],
        "category": "Performance Garmin",
        "color": "#5e5ce6",
        "body_md": """
**Training Status** é o veredito sintético do Garmin sobre o que sua carga atual está fazendo com seu condicionamento. Combina **VO2 Max trend** (sua capacidade aeróbica está subindo ou caindo?) + **Acute Load vs Chronic Load** (ACWR) + **HRV Status** + **Sleep**.

### Os 7 estados possíveis

| Status | Significado | O que fazer |
|---|---|---|
| **PRODUCTIVE** | Carga ideal pra ganhar VO2 Max. Em build saudável. | Continuar o que está fazendo |
| **MAINTAINING** | Carga preserva fitness, sem grandes ganhos. | OK por algumas semanas — depois precisa subir carga |
| **PEAKING** | VO2 Max alto + carga reduzida = pronto pra prova | Janela de race performance (5-14 dias) |
| **OVERREACHING** | Carga aguda alta demais vs crônica. Risco de overtraining. | **Reduzir volume/intensidade por 3-7 dias.** Não somar treino pesado |
| **UNPRODUCTIVE** | Treinando mas VO2 Max não sobe (sinal de fadiga, sono ruim, ou plateau) | Investigar sono, recovery, possível doença |
| **DETRAINING** | Carga muito baixa, VO2 Max caindo | Voltar a treinar com regularidade |
| **RECOVERY** | Pós-carga pesada — sistema descansando | Honrar o descanso, não forçar |

### VO2 Max Trend (sub-indicador)

Aparece junto ao Training Status. Mostra trajetória da capacidade aeróbica nas últimas semanas:

- **PRODUCTIVE_1/2/3** → subindo (com magnitude crescente)
- **MAINTAINING** → estável
- **DETRAINING** → caindo

### Por que importa

Training Status é o **sinal "macro" do plano**. Veredito diário (HRV/BB/FCrep) responde "como estou hoje?". Training Status responde "para onde minha temporada está indo?". Se ficar UNPRODUCTIVE ou OVERREACHING por mais de 7 dias, é hora de reavaliar a estratégia da semana.

### Gatilhos pra agir

- **OVERREACHING 1-2 dias** → normal pós-semana pesada. Honra o recovery e segue
- **OVERREACHING 3+ dias** → reduzir carga ativa. Algo não está fechando
- **UNPRODUCTIVE 5+ dias** → revisar sono, alimentação, sinais de doença
- **DETRAINING** → voltar a treinar com regularidade (provavelmente teve período off)
""",
    },
    {
        "id": "acwr",
        "title": "ACWR — Carga Aguda / Crônica",
        "aliases": ["ACWR", "CARGA AGUDA", "CARGA CRÔNICA", "ATL", "CTL", "ACUTE LOAD", "CHRONIC LOAD"],
        "category": "Performance Garmin",
        "color": "#5e5ce6",
        "body_md": """
**ACWR (Acute:Chronic Workload Ratio)** é a razão entre sua **carga aguda** (últimos ~7 dias) e sua **carga crônica** (últimos ~28 dias, média móvel). É um dos indicadores mais validados pela ciência esportiva pra prever **risco de lesão e overtraining**.

### Os dois componentes

- **ATL (Acute Training Load)** = carga dos últimos ~7 dias. Reflete fadiga recente.
- **CTL (Chronic Training Load)** = média ponderada exponencial dos últimos ~28-42 dias. Reflete condicionamento de base ("fitness").

ACWR = ATL / CTL

### Como ler

| Faixa | Status | Interpretação |
|---|---|---|
| **<0.8** | Detraining | Carga aguda muito abaixo do que o corpo está acostumado — perdendo fitness |
| **0.8 – 1.3** | **OPTIMAL** ✅ | Sweet spot: estímulo suficiente sem risco elevado |
| **1.3 – 1.5** | Atenção | Carga aguda esticando — pode ser produtivo se controlado, monitorar |
| **>1.5** | **RISK ZONE** ⚠️ | Risco de lesão e overtraining sobe **2-4× vs faixa ótima** |

### Por que 0.8-1.3 é o ideal

Estudos com atletas de elite (rugby, futebol, atletismo) mostram que quando ACWR sai dessa faixa em qualquer direção, a taxa de lesão músculo-tendínea sobe significativamente. Acima de 1.5, o corpo recebe estresse maior do que adaptou pra suportar.

### CTL — o número mais importante

CTL é seu "fitness" cumulativo. Sobe lentamente (+2-4 pontos/semana sustentável). Pra amadores rodando maratona em 4h00-4h30, faixa típica:

- **CTL 30-40** = iniciante avançado
- **CTL 50-65** = intermediário sólido pra meia/maratona
- **CTL 70+** = competidor focado, longões consistentes

### Como subir CTL com segurança

1. Aumentar volume/intensidade gradualmente — alvo +2-4 CTL/semana
2. Respeitar semana de regeneração a cada 3-4 semanas (ACWR cai pra 0.7-0.9)
3. Não tentar pegar CTL perdido com treinos pesados — risco de spike ACWR

### Atenção aos limites

- ACWR ignora **qualidade do treino** (intensidade, terreno, calor)
- HRV/FCrep podem sinalizar overtraining antes do ACWR explodir
- Use ACWR junto com Training Status, não isolado
""",
    },
    {
        "id": "vo2-max",
        "title": "VO2 Max & Idade Fitness",
        "aliases": ["VO2 MAX", "VO2MAX", "FITNESS AGE", "IDADE FITNESS"],
        "category": "Performance Garmin",
        "color": "#5e5ce6",
        "body_md": """
**VO2 Max** é o volume máximo de oxigênio que seu corpo consegue captar e utilizar por minuto, normalizado pelo peso (ml/kg/min). É **o melhor indicador isolado de capacidade aeróbica** que existe.

### Como o Garmin estima

Não é medição direta (que exige laboratório com máscara). O Garmin combina:
- Pace × FC durante corridas regulares
- Idade, peso, altura, sexo declarados
- Eficiência aparente (variações de pace pra mesma FC)

Erro típico: ±2-3 ml/kg/min vs teste de laboratório. **Tendência (subindo/descendo) é mais confiável que valor absoluto**.

### Faixas pra homens 50+

| VO2 Max | Classificação |
|---|---|
| <30 | Pobre |
| 30-35 | Abaixo da média |
| 35-40 | Médio |
| 40-45 | Bom |
| 45-50 | Excelente |
| 50+ | Elite (raro nessa faixa etária) |

### O que sobe VO2 Max

- **Intervalos Z4-Z5** (3-5×3-5min em pace de 10K) — o estímulo mais potente
- **Longões aeróbicos** (1h30+ em Z2-Z3) — base que sustenta o teto
- **Consistência ao longo de meses** — mudanças significativas em 8-12 semanas

### O que derruba

- **Inatividade** — perde 1-2 ml/kg/min por semana parado após 7 dias
- **Doença prolongada**
- **Sono cronicamente ruim**
- **Idade** — declínio natural ~0.5%/ano após 30, mais lento com treino

### Idade Fitness

**Fitness Age** = idade biológica estimada pela sua capacidade aeróbica. Calculada como "que idade tem alguém da população geral com seu VO2 Max?".

- Idade Fitness **menor que cronológica** = ✅ você está em melhor forma que a média do seu grupo
- Idade Fitness **maior** = sinal pra investir em aeróbico

Move 1-2 anos por mês com treino consistente. Sensível a tendências de VO2 Max.

### Limitações

- VO2 Max é necessário mas não suficiente pra performance — economia de corrida e cadência também pesam
- Atletas com VO2 Max similar podem ter performances muito diferentes na prova
- Use como **um dos** indicadores, junto com Race Predictor, Training Status, ACWR
""",
    },
    {
        "id": "recovery-time",
        "title": "Recovery Time",
        "aliases": ["RECOVERY TIME", "TEMPO DE RECUPERAÇÃO"],
        "category": "Performance Garmin",
        "color": "#5e5ce6",
        "body_md": """
**Recovery Time** é a estimativa do Garmin em **horas** até seu corpo estar "pronto" pra outro treino-chave (intensidade alta ou volume alto). Calculado após cada atividade com base em:

- Intensidade (FC média + tempo em zonas altas)
- Duração
- Estado autonômico (HRV) atual
- Recovery acumulado da janela recente

### Como ler

| Recovery Time | Interpretação |
|---|---|
| **0-12h** | Pronto pra outro treino-chave |
| **12-24h** | Pronto pra atividade leve (Z2 fácil, walking) |
| **24-48h** | Honrar a recuperação. Pode treinar Z2 leve no fim do período |
| **48-72h** | Pós-treino muito pesado (longão >2h, intervalos Z5) — descanso |
| **>72h** | Sinal de sobrecarga. Provável OVERREACHING. Reavaliar |

### O que aumenta Recovery Time

- Treinos em Z4-Z5 (limite/máximo) — peso desproporcional
- Longões >90 min, especialmente acima de 2h
- HRV baixa no momento do treino (corpo já cansado)
- Treinos em calor extremo
- Falta de sono na noite anterior

### Como acelerar a queda

- **Sono ≥8h** com REM ≥70 min e Deep ≥60 min
- **Hidratação 35-40 ml/kg/dia** + eletrólitos pós-treino
- **Carbo + proteína** na janela 30-60 min pós-treino
- **Movimento leve** (caminhada 20-30 min) — facilita perfusão
- **Evitar álcool** — sabota recovery autonômico

### Importante

Recovery Time é **estimativa**, não regra dura. Se HRV/BB voltarem a níveis bons antes do contador zerar, você está pronto. Se Recovery Time zerou mas HRV está caindo, **prefira HRV como verdade** e descanse mais.

### Sinal de alerta

Recovery Time consistentemente >48h por **mais de 3 dias** sugere:
- Carga acumulada acima da capacidade de adaptação
- Sono crônico insuficiente
- Possível doença incipiente

→ Reduzir carga 30-50% por uma semana e reavaliar.
""",
    },
    {
        "id": "race-predictor",
        "title": "Race Predictor",
        "aliases": ["RACE PREDICTOR", "PREVISÃO DE PROVA"],
        "category": "Performance Garmin",
        "color": "#ff9500",
        "body_md": """
**Race Predictor** é a estimativa do Garmin de quanto tempo você levaria pra completar 5K, 10K, meia-maratona (21K) e maratona (42K) **hoje**, baseado no seu condicionamento atual.

### Como o Garmin calcula

1. Usa o **VO2 Max** atual como base
2. Aplica modelos publicados (Daniels, Riegel) pra extrapolar performance em cada distância
3. Ajusta por dados recentes — pace × FC dos treinos longos, intervalos e tempo runs

**NÃO usa**: terreno, calor, estratégia de pacing, nutrição, dia da prova.

### Como interpretar

- **Valor absoluto** = potencial teórico em condições ideais. Real geralmente é 2-5% mais lento (calor, multidão, sub-fueling, pacing imperfeito).
- **Tendência (delta semanal/mensal)** = mais confiável que valor isolado. Trajetória pra baixo = ganhando fitness.

### Limites importantes — fórmula Riegel

A extrapolação 5K → maratona usa coeficiente **n** na fórmula T₂ = T₁ × (D₂/D₁)^n.

| n | Perfil |
|---|---|
| **0.85** | Elite (mantém pace bem em distâncias longas) |
| **1.02-1.10** | Bem treinado (4h30 maratona viável) |
| **1.15-1.20** | Amador intermediário (5h00+ típico) |
| **1.25+** | Iniciante em distâncias longas |

Garmin assume n próximo de 1.06 por padrão. Se seu n real for maior (típico em quem fez poucos longões), **maratona real será mais lenta que prevista**.

### Sinal de progresso real

Race Predictor melhorando + Training Status PRODUCTIVE/MAINTAINING + ACWR 0.8-1.3 = build saudável e ganhos reais.

Race Predictor melhorando + OVERREACHING ou UNPRODUCTIVE = sinal misto, investigar antes de confiar.

### Como usar pra meta de prova

1. **Não confie cegamente na previsão da maratona** — pode ser otimista 5-15% pra quem não tem longão de 30k+ no perna
2. **5K e 10K são previsões mais precisas** porque dependem menos de aguentar tempo longo
3. **21K é o gate** — se atleta consegue cravar a previsão da meia, a meia da maratona é mais previsível

### Atualização

Garmin recalcula:
- Após cada corrida (atualização pequena)
- Após teste guiado (Lactate Threshold, Race Predictor test) — atualização maior
- Diariamente com base em VO2 Max + HRV (ajuste fino)
""",
    },
    {
        "id": "veredito",
        "title": "Veredito automático",
        "aliases": ["VEREDITO"],
        "category": "Lógica do dashboard",
        "color": "#ff5e3a",
        "body_md": """
O **veredito** que aparece no topo da aba HOJE é gerado por uma regra interna que combina HRV, BB, FCrep e Sleep Score. **Não é mágica nem ML** — é uma soma de pontos baseada em limiares calibrados pra você.

### Como funciona

Cada métrica vira pontos:

| Métrica | 🟢 0 pts | 🟡 1 pt | 🔴 2 pts |
|---|---|---|---|
| HRV overnight | ≥32 ms | 26-31 ms | <26 ms |
| BB max | ≥65 | 50-64 | <50 |
| FCrep | ≤52 bpm | 53-54 | ≥55 |
| Sleep Score | ≥75 | 60-74 | <60 |

**Modificadores adicionais:**
- HRV caiu ≥5 ms vs ontem → **+1 ponto**
- FCrep subiu ≥3 bpm vs baseline 51 → **+1 ponto**

**NULL = métrica é excluída do score** (não soma 0, não soma 2 — é ignorada).

### Mapa pontos → veredito

| Total | Cor | Headline |
|---|---|---|
| **0** | 🟢 verde | Pronto pra treinar |
| **1-2** | 🟡 amarelo | Atenção: prioriza Z2 |
| **3-4** | 🟠 laranja | Descanso recomendado |
| **5+** | 🔴 vermelho | Corte forçado |

Se < 2 métricas avaliáveis (muitas NULL), veredito vira ⚪ cinza "Dados insuficientes".

### Limitações importantes

- **A regra não conhece o contexto do dia.** Se você dormiu mal de propósito (ex: viagem) ou treinou pesado por estratégia, o score vai parecer ruim mas pode estar tudo bem.
- **A regra é conservadora.** Em dia borderline (HRV 31), ela manda "atenção". A leitura humana pode ser "tá tudo bem, só o sensor pegou ruído".
- **O HRV pesa muito.** Se cair 5+ ms, dá +1 modifier mesmo se valor absoluto ainda for OK. É proposital — quedas bruscas são mais informativas que valores absolutos.
""",
    },
]


def get_glossary():
    """Retorna lista de entradas do glossário com HTML renderizado a partir do MD."""
    try:
        import markdown as md_lib
    except ImportError:
        # Sem markdown lib, devolve markdown bruto
        for entry in GLOSSARY:
            entry["html"] = f"<pre>{entry['body_md']}</pre>"
        return GLOSSARY

    out = []
    for entry in GLOSSARY:
        html = md_lib.markdown(
            entry["body_md"].strip(),
            extensions=["tables", "fenced_code", "nl2br"],
        )
        # Wrap tabelas em scroll horizontal pra mobile
        html = html.replace("<table>", '<div class="md-table-wrap"><table>')
        html = html.replace("</table>", "</table></div>")
        out.append({**entry, "html": html})
    return out


def alias_to_id():
    """Retorna dict mapeando cada alias (uppercase) para o id da entrada.

    Util pra fazer linking dinamico: dado um label "BB MAX", encontrar id="body-battery".
    """
    mapping = {}
    for entry in GLOSSARY:
        for alias in entry.get("aliases", []):
            mapping[alias.upper()] = entry["id"]
    return mapping
