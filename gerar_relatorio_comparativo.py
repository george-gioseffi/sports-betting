#!/usr/bin/env python3
"""
Generates the comparative report v1 vs v2 after matcher/parser improvements.
"""

import pandas as pd
import json
import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load both versions
v1_base = pd.read_csv(os.path.join(BASE_DIR, "outputs", "audit_real", "base_completa.csv"))
v2_base = pd.read_csv(os.path.join(BASE_DIR, "outputs", "audit_v2", "base_completa.csv"))
v1_corr = pd.read_csv(os.path.join(BASE_DIR, "outputs", "audit_real", "corrigir_green_red.csv"))
v2_corr = pd.read_csv(os.path.join(BASE_DIR, "outputs", "audit_v2", "corrigir_green_red.csv"))

with open(os.path.join(BASE_DIR, "outputs", "audit_real", "resumo_auditoria_20260323_143226.json")) as f:
    v1_json = json.load(f)
with open(os.path.join(BASE_DIR, "outputs", "audit_v2", "resumo_auditoria_20260324_002902.json")) as f:
    v2_json = json.load(f)

# ============================================================
# METRICS
# ============================================================
v1_matched = v1_base['evento_match'].fillna('').ne('').sum()
v2_matched = v2_base['evento_match'].fillna('').ne('').sum()
v1_unknown = (v1_base['mercado_detectado'] == 'unknown').sum()
v2_unknown = (v2_base['mercado_detectado'] == 'unknown').sum()
v1_ext = v1_json['summary'].get('fonte_externo', 0)
v2_ext = v2_json['summary'].get('fonte_externo', 0)
v1_total_corr = len(v1_corr)
v2_total_corr = len(v2_corr)

# Market comparison
v1_markets = v1_base['mercado_detectado'].value_counts()
v2_markets = v2_base['mercado_detectado'].value_counts()

# New corrections found
v2_keys = set(zip(v2_corr['data_hora'], v2_corr['descricao']))
v1_keys = set(zip(v1_corr['data_hora'], v1_corr['descricao']))
new_keys = v2_keys - v1_keys
new_corrections_count = len(new_keys)

# ============================================================
# MARKDOWN REPORT
# ============================================================
md = f"""# RELATORIO COMPARATIVO - MELHORIAS bet_audit v1 vs v2
**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Objetivo:** Aumentar cobertura de match externo e reduzir mercados desconhecidos

---

## 1. RESUMO DAS MELHORIAS IMPLEMENTADAS

### 1.1 Matcher de Times (team matching)
- Adicionado sistema de **aliases** para nomes de times (22 times com variantes)
- "Manchester City" agora matcha com "Man City", "Man. City", "ManCity", "City FC"
- "Bayern" matcha com "Bayern Munique", "Bayern de Munique", "FC Bayern"
- Todos os 10 times do CSV externo tem aliases registrados
- Janela de data flexibilizada: de match exato para **+/- 60 dias**
- Bets feitas semanas antes do evento agora conectam ao resultado

### 1.2 Parser de Mercado (market detection)
- **Corrigido:** "Mais **de** 2.5" e "Menos **de** 3.5" -- a palavra "de" entre keyword e numero
- **Adicionado:** Shorthand "o2.5", "u2.5", "O1.5", "U6.5" (over/under compacto)
- **Adicionado:** BTTS em ambas as ordens ("Sim / Ambas marcam" E "Ambas marcam / Sim")
- **Adicionado:** "Ambos os Times Marcam", "Ambas equipes Marcam" (variantes PT)
- **Adicionado:** ML/Moneyline via "vence", "vencem", "vencer", "ganha", "ganhar", "ML"
- **Adicionado:** "Resultado Final" como indicador de moneyline
- **Adicionado:** HT/FT: "Intervalo/Final", "1o Tempo 1X2", "Resultado 1o Tempo"
- **Adicionado:** Handicap: "Handicap Asiatico", "AH", "-1.5 AH", "HA -1.5"
- **Adicionado:** Double Chance: "Chance Dupla", "DC", "ou Empate"
- **Adicionado:** Corners: "escanteios", "cantos", "esc"
- **Adicionado:** Cards: "cartoes", "cartao", "cards"
- **Adicionado:** Player Props: "Duplo Duplo", "Triple Double", "pts", "Anytime", "Marcar a Qualquer Momento"
- **Adicionado:** Shots: "chutes no gol", "SOT", "SoTs"

### 1.3 Import fix
- AI providers agora usam import lazy (so carregam quando llm_mode != "off")
- Elimina dependencia de `openai`/`anthropic` quando IA esta desligada

---

## 2. RESULTADOS COMPARATIVOS

### 2.1 Match Externo

| Metrica | v1 (antes) | v2 (depois) | Delta |
|---------|-----------|-------------|-------|
| Matches encontrados | {v1_matched:,} | {v2_matched:,} | **+{v2_matched-v1_matched}** (+{(v2_matched-v1_matched)/v1_matched*100:.1f}%) |
| Taxa de match | {v1_matched/len(v1_base)*100:.1f}% | {v2_matched/len(v2_base)*100:.1f}% | +{(v2_matched-v1_matched)/len(v1_base)*100:.1f}pp |
| Vereditos via externo | {v1_ext:,} | {v2_ext:,} | **+{v2_ext-v1_ext}** (+{(v2_ext-v1_ext)/v1_ext*100:.1f}%) |

### 2.2 Mercados Desconhecidos

| Metrica | v1 (antes) | v2 (depois) | Delta |
|---------|-----------|-------------|-------|
| Mercados "unknown" | {v1_unknown:,} | {v2_unknown:,} | **-{v1_unknown-v2_unknown}** (-{(v1_unknown-v2_unknown)/v1_unknown*100:.1f}%) |
| Taxa de unknown | {v1_unknown/len(v1_base)*100:.1f}% | {v2_unknown/len(v2_base)*100:.1f}% | -{(v1_unknown-v2_unknown)/len(v1_base)*100:.1f}pp |

### 2.3 Distribuicao de Mercados Detectados (v2)

| Mercado | Quantidade | % |
|---------|-----------|---|
"""

for market, count in v2_markets.items():
    md += f"| {market} | {count:,} | {count/len(v2_base)*100:.1f}% |\n"

md += f"""
### 2.4 Correcoes Encontradas

| Tipo | v1 (antes) | v2 (depois) | Delta |
|------|-----------|-------------|-------|
| CORRIGIR_PARA_GREEN | {v1_json['summary'].get('veredito_CORRIGIR_PARA_GREEN', 0)} | {v2_json['summary'].get('veredito_CORRIGIR_PARA_GREEN', 0)} | **+{v2_json['summary'].get('veredito_CORRIGIR_PARA_GREEN', 0) - v1_json['summary'].get('veredito_CORRIGIR_PARA_GREEN', 0)}** |
| CORRIGIR_PARA_RED | {v1_json['summary'].get('veredito_CORRIGIR_PARA_RED', 0)} | {v2_json['summary'].get('veredito_CORRIGIR_PARA_RED', 0)} | **+{v2_json['summary'].get('veredito_CORRIGIR_PARA_RED', 0) - v1_json['summary'].get('veredito_CORRIGIR_PARA_RED', 0)}** |
| CORRIGIR_PARA_ANULADA | {v1_json['summary'].get('veredito_CORRIGIR_PARA_ANULADA', 0)} | {v2_json['summary'].get('veredito_CORRIGIR_PARA_ANULADA', 0)} | **+{v2_json['summary'].get('veredito_CORRIGIR_PARA_ANULADA', 0) - v1_json['summary'].get('veredito_CORRIGIR_PARA_ANULADA', 0)}** |
| **TOTAL CORRECOES** | **{v1_total_corr}** | **{v2_total_corr}** | **+{v2_total_corr - v1_total_corr}** (+{(v2_total_corr-v1_total_corr)/v1_total_corr*100:.0f}%) |

### 2.5 Impacto nos Vereditos

| Veredito | v1 | v2 | Delta |
|----------|----|----|-------|
| MANTER_GREEN | {v1_json['summary'].get('veredito_MANTER_GREEN', 0):,} | {v2_json['summary'].get('veredito_MANTER_GREEN', 0):,} | {v2_json['summary'].get('veredito_MANTER_GREEN', 0) - v1_json['summary'].get('veredito_MANTER_GREEN', 0):+,} |
| MANTER_RED | {v1_json['summary'].get('veredito_MANTER_RED', 0):,} | {v2_json['summary'].get('veredito_MANTER_RED', 0):,} | {v2_json['summary'].get('veredito_MANTER_RED', 0) - v1_json['summary'].get('veredito_MANTER_RED', 0):+,} |
| MANTER_ANULADA | {v1_json['summary'].get('veredito_MANTER_ANULADA', 0):,} | {v2_json['summary'].get('veredito_MANTER_ANULADA', 0):,} | {v2_json['summary'].get('veredito_MANTER_ANULADA', 0) - v1_json['summary'].get('veredito_MANTER_ANULADA', 0):+,} |
| fonte_externo | {v1_ext:,} | {v2_ext:,} | {v2_ext - v1_ext:+,} |
| fonte_regra | {v1_json['summary'].get('fonte_regra', 0):,} | {v2_json['summary'].get('fonte_regra', 0):,} | {v2_json['summary'].get('fonte_regra', 0) - v1_json['summary'].get('fonte_regra', 0):+,} |

> **Interpretacao:** 819 linhas que antes dependiam apenas de "regra deterministica"
> agora tem validacao cruzada com resultado externo. Isso aumentou a confiabilidade
> do veredito e revelou **+508 novas correcoes** que estavam escondidas.

---

## 3. PADROES NOVOS INCORPORADOS

| Categoria | Padroes adicionados | Exemplos |
|-----------|-------------------|----------|
| Over/Under PT | "Mais de X.X", "Acima de X.X", "o2.5", "O1.5" | "Mais de 2.5 gols" |
| Under PT | "Menos de X.X", "Abaixo de X.X", "u2.5", "U6.5" | "Menos de 3.5 Gols" |
| ML/1X2 PT | "vence", "vencem", "ML", "Resultado Final" | "Liverpool vence" |
| BTTS expandido | "Ambos os Times Marcam", "Sim / Ambas..." | "Sim / Ambos os Times Marcam" |
| HT/FT | "Intervalo/Final", "1o Tempo 1X2" | "Liverpool HT/FT" |
| Handicap | "Handicap Asiatico", "AH", "HA" | "Liverpool -1.5 AH" |
| Double Chance | "Chance Dupla", "DC", "ou Empate" | "Cagliari ou Empate" |
| Corners | "escanteios", "cantos", "esc" | "5+ escanteios HT" |
| Cards | "cartoes", "cartao" | "Liverpool -1.5 cartoes" |
| Player Props | "Duplo Duplo", "pts", "Anytime", "Marcar a Qualquer Momento" | "Haaland Marcar a Qualquer Momento" |
| Shots | "chutes", "SOT", "SoTs" | "2+ Chutes no Gol" |
| Team aliases | Man City, Manchester, Bayern, Barcelona + variantes | "Manchester City" -> "Man City" |

---

## 4. RISCOS REMANESCENTES

1. **24,504 linhas sem match externo** -- o CSV externo tem apenas 10 eventos.
   Para cobertura total, seria necessario integrar API de resultados esportivos.

2. **4,553 mercados ainda "unknown"** (16%) -- sao apostas que nao se encaixam
   em nenhum padrao conhecido (ex: apostas compostas complexas, mercados exoticos).

3. **IA nao utilizada** -- 0 chamadas de IA nesta execucao. Com IA cirurgica,
   os 4,553 unknowns poderiam ser parcialmente resolvidos.

4. **Novas correcoes nao verificadas manualmente** -- as 508 novas correcoes
   encontradas na v2 tem a mesma base de confianca (0.95 via resultado externo),
   mas como o parser de mercado agora detecta mais mercados, erros de classificacao
   de mercado podem gerar falsos positivos.

5. **Combinadas/multiples** -- muitas descricoes sao apostas combinadas (ex:
   "Liverpool, Chelsea e Arsenal vencem"). O parser detecta "moneyline" mas
   a resolucao nao consegue validar todas as pernas da combinada.

---

## 5. PROXIMOS PASSOS RECOMENDADOS

1. **Expandir CSV externo** -- adicionar mais eventos para cobrir mais apostas
2. **IA cirurgica** -- usar LLM para os 4,553 unknowns e para validar combinadas
3. **Parser de combinadas** -- detectar apostas multi-perna e resolver cada perna
4. **Validacao manual** -- revisar amostra das novas 508 correcoes para calibrar
5. **API externa** -- integrar API de resultados (ex: API-Football) para cobertura total

---

## 6. ARQUIVOS GERADOS

| Arquivo | Descricao |
|---------|-----------|
| `outputs/audit_v2/base_completa.csv` | Base completa v2 (28,507 linhas) |
| `outputs/audit_v2/corrigir_green_red.csv` | 946 correcoes sugeridas |
| `outputs/audit_v2/resumo_auditoria_*.json` | Resumo da execucao v2 |
| `output/relatorio_comparativo.md` | Este relatorio |

---

*Relatorio gerado automaticamente em {datetime.now().strftime('%Y-%m-%d %H:%M')}*
*Comparando: audit_real (v1) vs audit_v2 (v2)*
"""

with open(os.path.join(OUTPUT_DIR, "relatorio_comparativo.md"), "w", encoding="utf-8") as f:
    f.write(md)

print("relatorio_comparativo.md gerado.")

# ============================================================
# SUMMARY PRINT
# ============================================================
print(f"""
=====================================================
     RELATORIO FINAL DA EXECUCAO
=====================================================

MELHORIAS IMPLEMENTADAS:
  1. Team aliases (22 times com variantes)
  2. Janela de data flexivel (+/- 60 dias)
  3. Market parser expandido (11 novos tipos de mercado)
  4. Import lazy para AI providers
  5. Line extractor melhorado (shorthand, virgulas)

RESULTADOS:

  MATCH EXTERNO:
    Antes: {v1_matched:,} matches
    Depois: {v2_matched:,} matches
    Ganho: +{v2_matched - v1_matched} matches (+{(v2_matched-v1_matched)/v1_matched*100:.1f}%)

  MERCADOS DESCONHECIDOS:
    Antes: {v1_unknown:,} ({v1_unknown/len(v1_base)*100:.1f}%)
    Depois: {v2_unknown:,} ({v2_unknown/len(v2_base)*100:.1f}%)
    Reducao: {v1_unknown - v2_unknown:,} casos (-{(v1_unknown-v2_unknown)/v1_unknown*100:.1f}%)

  VEREDITOS VIA EXTERNO:
    Antes: {v1_ext:,}
    Depois: {v2_ext:,}
    Ganho: +{v2_ext - v1_ext:,} (+{(v2_ext-v1_ext)/v1_ext*100:.0f}%)

  CORRECOES ENCONTRADAS:
    Antes: {v1_total_corr}
    Depois: {v2_total_corr}
    Novas: +{v2_total_corr - v1_total_corr} (+{(v2_total_corr-v1_total_corr)/v1_total_corr*100:.0f}%)

  DETALHAMENTO:
    CORRIGIR_PARA_GREEN: {v1_json['summary'].get('veredito_CORRIGIR_PARA_GREEN', 0)} -> {v2_json['summary'].get('veredito_CORRIGIR_PARA_GREEN', 0)} (+{v2_json['summary'].get('veredito_CORRIGIR_PARA_GREEN', 0) - v1_json['summary'].get('veredito_CORRIGIR_PARA_GREEN', 0)})
    CORRIGIR_PARA_RED: {v1_json['summary'].get('veredito_CORRIGIR_PARA_RED', 0)} -> {v2_json['summary'].get('veredito_CORRIGIR_PARA_RED', 0)} (+{v2_json['summary'].get('veredito_CORRIGIR_PARA_RED', 0) - v1_json['summary'].get('veredito_CORRIGIR_PARA_RED', 0)})
    CORRIGIR_PARA_ANULADA: {v1_json['summary'].get('veredito_CORRIGIR_PARA_ANULADA', 0)} -> {v2_json['summary'].get('veredito_CORRIGIR_PARA_ANULADA', 0)} (+{v2_json['summary'].get('veredito_CORRIGIR_PARA_ANULADA', 0) - v1_json['summary'].get('veredito_CORRIGIR_PARA_ANULADA', 0)})

LIMITACOES REMANESCENTES:
  - 24,504 linhas sem match (CSV tem apenas 10 eventos)
  - 4,553 mercados still unknown (16%)
  - IA nao usada nesta execucao
  - Apostas combinadas nao totalmente resolvidas

ARQUIVOS GERADOS:
  - outputs/audit_v2/ (execucao completa)
  - output/relatorio_comparativo.md

=====================================================
""")
