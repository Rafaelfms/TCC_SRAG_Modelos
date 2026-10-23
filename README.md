# Modelos interpretáveis em dados de vigilância epidemiológica: vacinação contra COVID-19 e óbito por SRAG no Brasil (2019–2026)

Código do Trabalho de Conclusão de Curso da pós-graduação em Ciência de Dados do Centro Universitário Facens (Sorocaba, SP)

**Autor:** Rafael Felipe de Moraes e Sousa

O trabalho usa os dados públicos do SIVEP-Gripe (Sistema de Informação da Vigilância Epidemiológica da Gripe) para:

1. descrever a evolução mensal dos casos de Síndrome Respiratória Aguda Grave (SRAG), a participação da COVID-19 e a letalidade da SRAG-COVID entre 2019 e 2026;
2. estimar a associação entre a vacinação contra a COVID-19 e o óbito entre casos hospitalizados por SRAG-COVID (2021–2026), controlando por idade, sexo e comorbidades, com regressão logística, regressão de Poisson com variância robusta e XGBoost interpretado por SHAP.

> **Importante:** os resultados são **associações estatísticas condicionais à hospitalização**, e não estimativas causais nem de efetividade vacinal na população.

---

## Estrutura do repositório

```
.
├── README.md
├── requirements.txt
├── scripts/
│   ├── resumir_srag.py              # Etapa 1: série mensal de todos os casos de SRAG
│   └── extrair_base_srag_covid.py   # Etapa 2: base individual de SRAG-COVID
├── modelos/
│   └── modelo_srag_covid.ipynb      # Etapa 3: tratamento final, modelos, tabelas e figuras

```

---

## Dados

**Fonte:** Ministério da Saúde, OpenDataSUS, conjunto *SRAG 2019 a 2026 – Banco de Dados de Síndrome Respiratória Aguda Grave*:
https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026


**Versões usadas no artigo:**

| Uso | Arquivos | Data de publicação |
|---|---|---|
| Série temporal (etapa 1) | INFLUD19 a INFLUD26 | INFLUD25 e INFLUD26 de 14/09/2026;
| Modelagem (etapas 2 e 3) | INFLUD19 a INFLUD26 | INFLUD25 e INFLUD26 de 28/09/2026; 

Os dados de 2025 e 2026 são **provisórios**: o Ministério da Saúde atualiza os arquivos periodicamente, e os números podem mudar em versões futuras.

A documentação das variáveis está no *Dicionário de dados – SRAG hospitalizado* (Ministério da Saúde, 2023), disponível na mesma página do conjunto de dados.

---
> **Nota:** os arquivos com dados resumidos foram disponibilizados separadamente por conta do tamanho.
---

### Etapa 1: série mensal de todos os casos

```bash
python scripts/resumir_srag.py dados/brutos --saida dados/resumos
```

Para cada arquivo, agrega **todos** os casos de SRAG (todas as etiologias) por mês de notificação: total de casos, casos de COVID-19 (`CLASSI_FIN = 5`), casos encerrados, óbitos por SRAG (`EVOLUCAO = 2`), internações em UTI e casos vacinados. Gera um resumo por arquivo e três arquivos combinados; o notebook usa `resumo_mensal_TODOS.csv`.

### Etapa 2: base individual de SRAG-COVID

```bash
python scripts/extrair_base_srag_covid.py dados/brutos --saida dados/base_covid
```

Lê cada arquivo, carrega só as colunas necessárias e mantém apenas os casos com `CLASSI_FIN = 5` (SRAG por COVID-19). Durante a leitura:

- converte a idade para anos a partir de `NU_IDADE_N` e `TP_IDADE` (dias, meses ou anos);
- lê explicitamente os dois formatos de data, para evitar a troca silenciosa entre dia e mês;
- transforma em valor ausente as datas com ano fora do intervalo 2015–2030 (erros de digitação, como `7202`);
- preserva `CS_SEXO` e `SG_UF` como texto;
- registra os erros de leitura em `erros_log.txt`.


### Etapa 3: notebook

Abra `notebooks/modelo_srag_covid.ipynb` e ajuste os caminhos no início:

```python
CAMINHO_CSV = "../dados/base_covid/base_covid_TODOS.csv"
CAMINHO_RESUMO = "../dados/resumos/resumo_mensal_TODOS.csv"
```

Depois execute as células em ordem. A execução completa leva alguns minutos; as etapas mais demoradas são a regressão de Poisson, a validação cruzada e o cálculo dos valores SHAP.

---

## Conteúdo do notebook


| Seção | Conteúdo | No artigo |
|---|---|---|
| 1–4 | Setup, leitura, engenharia de atributos e montagem da base de modelagem | Metodologia, Figura 1 |
| 5 | Série anual de SRAG, SRAG-COVID e letalidade | Tabela 1, Figura 2 |
| 6 | Perfil de vacinados e não vacinados; óbitos por faixa etária | Tabela 2 |
| 7–9 | Regressão logística: bruta, ajustada e ajustada por ano ou trimestre | Tabela 3 |
| 10 | Poisson com variância robusta (razão de riscos) | Tabela 3 |
| 11 | Resumo dos modelos e *forest plot* | Tabela 3 |
| 12–13 | XGBoost: treino e avaliação | Resultados |
| 14 | Valores SHAP | Figura 3 |
| 15 | Sensibilidade: status vacinal "ignorado" e "não informado" | Resultados |
| 16 | Desfecho complementar: internação em UTI | Resultados |
| 17 | Validação cruzada (5 partições) e validação temporal | Resultados |
| 18 | OR ajustado estimado separadamente por ano | Figura 4 |
| 20 | Regressão logística × XGBoost: matriz de confusão, F1 e limiar | Tabela 4 |
| 21 | Perfil dos casos sem status vacinal e cenários extremos | Resultados, Discussão |
| 22 | Composição dos grupos por ano e AUC de treino da validação temporal | Discussão |

---

## Variáveis e modelos

**Desfecho:** óbito por SRAG (`EVOLUCAO = 2`) contra cura (`EVOLUCAO = 1`). Os óbitos por outras causas e as evoluções ignoradas ficam fora dos modelos.

**Exposição:** vacinação contra COVID-19 registrada na ficha (`VACINA_COV = 1` contra `2`).

**Covariáveis:**

| Variável | Construção |
|---|---|
| Idade | Em anos (termo linear) |
| Sexo masculino | 1 = M; 0 = F |
| Nº de comorbidades | Soma das 11 comorbidades marcadas como "sim" |
| Comorbidades não registradas | 1 = todos os 11 campos de comorbidade vazios |
| Período de notificação | Ano ou trimestre de `DT_NOTIFIC` (variável categórica) |


**Modelos:**

| Modelo | Papel | Implementação |
|---|---|---|
| Regressão logística | Modelo principal: OR ajustado, estimado em etapas para medir o confundimento | `statsmodels.formula.api.logit` |
| Poisson com variância robusta | Razão de riscos (RR), porque o OR exagera a associação quando o desfecho é frequente (30,5%) | `statsmodels` GLM Poisson, `cov_type="HC0"` |
| XGBoost + SHAP | Verificação independente, sem as suposições de linearidade e sem interações pré-definidas | `xgboost.XGBClassifier`, `shap.TreeExplainer` |

**Hiperparâmetros do XGBoost**, fixados *a priori*:

| Parâmetro | Valor | Justificativa |
|---|---|---|
| `n_estimators` | 300 | Número moderado de árvores, combinado com taxa de aprendizado baixa |
| `max_depth` | 4 | Comporta interações entre até quatro variáveis, compatível com os cinco preditores |
| `learning_rate` | 0,05 | Aprendizado gradual; reduz o risco de sobreajuste |
| `subsample` | 0,8 | Cada árvore usa 80% das linhas sorteadas |
| `colsample_bytree` | 0,8 | Cada árvore usa 80% das variáveis sorteadas |
| `eval_metric` | `logloss` | Função de perda padrão para classificação binária |
| `random_state` | 42 | Reprodutibilidade |

A otimização foi dispensada porque o XGBoost serve para verificar a direção dos efeitos, e não para fazer previsões, e porque a AUC se manteve estável na validação cruzada. Não foi aplicado balanceamento de classes. O limiar de 0,5 é comparado ao limiar igual à proporção de óbitos no treino (0,305).

**Validação e reprodutibilidade:**

- treino/teste em proporção 75/25, estratificado pelo desfecho, com `random_state=42`;
- validação cruzada com `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`;
- validação temporal com treino em 2021–2023 e teste em 2024–2025; 2026 fica de fora por ser provisório.

---

## Principais resultados

| Medida | Resultado |
|---|---|
| Casos de SRAG notificados (2019 – set./2026) | 4.658.215 |
| Participação da COVID-19 na SRAG | 71,0% (2021) → 5,4% (2025) |
| Letalidade da SRAG-COVID | 33,6% (2020) → 16,0% (2025) |
| OR bruto da vacinação | 0,933 (0,925–0,941) |
| OR ajustado (idade, sexo, comorbidades) | 0,486 (0,481–0,491) |
| OR ajustado + trimestre (especificação principal) | 0,597 (0,590–0,603) |
| RR ajustado + trimestre (Poisson robusta) | 0,729 (0,725–0,734) |
| AUC no teste: regressão logística / XGBoost | 0,704 / 0,708 |
| OR ajustado por ano | 0,497 (2021) → 0,883 (2024); não significativo em 2025–2026 |

