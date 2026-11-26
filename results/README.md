# Resultados experimentais

| Diretório | Conteúdo |
|---|---|
| `cp01.2/` | Rodada B1/B2: outputs integrais, pares CSV, métricas JSON e relatório |
| `cp01.2-validation/` | Logs e hashes antes/depois do executor experimental |
| `cp02.1-validation/` | Logs, hashes e exemplos da seleção explícita de workload |
| `repository-layout-validation/` | Verificação funcional após a reorganização do repositório |

Os registros CP01.2 e CP02.1 permanecem inalterados. Seus caminhos, hashes de código e estados de Git se referem à execução original, quando os módulos estavam na raiz. Eles não devem ser reescritos para aparentar que o experimento ocorreu no novo layout.

Correspondência dos caminhos anteriores:

| Antes | Agora |
|---|---|
| `exposure_analyzer.py` | `src/exposure_analyzer.py` |
| `exposure_analyzer_v2.py` | `src/exposure_analyzer_v2.py` |
| `run_experiments.py` | `src/run_experiments.py` |
| `run_scenarios.py` | `scripts/run_scenarios.py` |
| `build_scenarios.py` | `scripts/build_scenarios.py` |
| `docs/cp01-*.md` | `docs/foundation/cp01-*.md` |
| `docs/cp01.2-execution.md` | `docs/checkpoints/cp01.2-execution.md` |
| `docs/cp02.1-unit-of-analysis.md` | `docs/checkpoints/cp02.1-unit-of-analysis.md` |
| `docs/session-summary-2026-11-26.md` | `docs/sessions/session-summary-2026-11-26.md` |
| PDFs na raiz | `references/` (somente local, ignorado pelo Git) |

O classificador histórico mantém os mesmos bytes. Executor/adaptador e scripts receberam somente ajustes de caminhos; por isso seus hashes atuais podem diferir dos registrados nos checkpoints. As regras, as fixtures históricas e os rótulos permanecem iguais.

Novas rodadas devem usar destino próprio ainda inexistente. Todos os dados são sintéticos; os resultados não demonstram acurácia científica independente.
