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
