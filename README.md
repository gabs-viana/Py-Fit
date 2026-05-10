# 🏃‍♂️ Py-Fit: Infraestrutura Fisiológica de Elite

O **Py-Fit** é um ecossistema modular para monitoramento autonômico, análise biomecânica e gestão de performance atlética orientada por LLM. 🛡️🚀🧠

---

## 🏗️ Arquitetura do Sistema

O sistema é dividido em dois pilares principais:

### 1. 🧬 Gestão de Saúde Diária (`Daily.py` + `Auto-Builder`)
Este pilar cuida da sua biometria, sono, nutrição e tendências fisiológicas.

#### **Como usar:**
1.  **Ingestão Automática (Zepp Cloud)**:
    - Execute o builder para gerar os dados do dia direto da nuvem:
      ```bash
      python src/ingestion/auto_daily_builder.py [YYYY-MM-DD]
      ```
    - Isso gerará o `prefill_daily.json` com Baselines de 30 dias, HRV, Readiness e Macros Nutricionais.

2.  **Registro do Log Diário**:
    - Rode o script principal para consolidar o seu log:
      ```bash
      python Daily.py
      ```
    - O sistema carregará os dados da Zepp e permitirá que você adicione notas contextuais antes de salvar o log final na sua base histórica.

---

### 2. 🏃‍♂️ Análise de Performance de Treino (`Fit.py`)
Este pilar é focado na análise biomecânica granular de arquivos `.fit` (GPS, Cadência, HR por segundo, GAP, etc).

#### **Como usar:**
1.  **Processamento de Arquivos**:
    - Coloque seus arquivos `.fit` (exportados da Zepp ou Strava) na pasta de processamento.
    - Execute a análise:
      ```bash
      python Fit.py
      ```
2.  **Métricas Geradas**:
    - O script calcula métricas avançadas como **Grade Adjusted Pace (GAP)**, **Running Power** e zonas de intensidade.
    - Os resultados são exportados para facilitar a leitura pela LLM de performance.

---

## 🛠️ Tecnologias & Diferenciais

- **Zepp Cloud Bypass**: Ingestão direta ignorando Root Detection e SSL Pinning.
- **Longitudinal Trend Engine**: Análise de tendências de 30 dias (Baselines adaptativas).
- **Fatigue Signatures**: Detecção automática de Fadiga Simpática e Supercompensação.
- **LLM-First Design**: Dados estruturados especificamente para serem consumidos por modelos de linguagem de elite.

---

## 📂 Estrutura de Pastas

- `/src/ingestion`: Scripts de captura de dados (Cloud, Local Export).
- `/src/analysis`: Motor de tendências e algoritmos de prontidão.
- `/data/logs`: Sua base histórica de logs diários.
- `/data/prefill`: JSONs temporários gerados pela automação.
- `/config`: Arquivos de sessão e chaves de API.

---

*Py-Fit: Porque o que não é medido, não é melhorado.* 📈🔥👊
