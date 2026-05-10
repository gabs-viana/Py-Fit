# 🚀 Roadmap Py-Fit: Próximos Passos (Elite V2)

Documento de planejamento para a evolução do motor de performance.

## 📈 Refinamento Biométrico
- [ ] **RHR (Resting Heart Rate)**: Ajustar o cálculo para eliminar o gap (atual -3 vs real). Investigar o endpoint `heartRate` bruto vs o valor reportado pelo PAI.
- [ ] **PAI (Gain do Dia)**: Exibir o ganho de PAI específico do dia no prompt e no JSON final.
- [ ] **VFC (HRV)**: Implementar a captura do RMSSD/HRV do endpoint `/v2/users/me/events` para alimentar o Readiness Index com dados reais em vez de placeholders.

## 🛌 Performance de Sono
- [ ] **Biocharge**: Integrar os níveis de Biocharge (ao acordar e ao deitar) capturados via `insight_data`.
- [ ] **Sleep Score**: Substituir a entrada manual de "Qualidade" pela pontuação nativa da Zepp Cloud (`ss` ou `sleepScore`).

## 🍎 Nível 2: Nutrição & Contexto
- [ ] **Ingestão de Refeições**: Explorar a extração de dados nutricionais e descritivos diretamente da Zepp Cloud, integrando ao campo `alimentacao`.

---
*Retomaremos em: 10/05/2026*
