# System Exposure — protótipo SSVC

Protótipo acadêmico determinístico para analisar exposição a partir de manifestos Kubernetes e snapshots AWS **locais e sintéticos**. O classificador histórico permanece como referência; a interface CP02.1 permite selecionar um workload sem atribuir automaticamente a ele o máximo global.

## Estrutura

```text
src/                         # Classificador histórico, seleção e executor B1/B2
scripts/                     # Execução e geração da suíte histórica
tools/                       # Launcher de execução offline
scenarios/                   # 16 cenários históricos, com rótulos e snapshots
tests/                       # Testes automatizados e fixtures separadas
docs/
  foundation/                # Fundamentação e propostas científicas CP01.1
  checkpoints/               # Relatórios técnicos CP01.2 e CP02.1
  sessions/                  # Resumos de encerramento
results/                     # Rodadas experimentais e logs preservados
references/                  # PDFs locais ignorados pelo Git
requirements.txt             # PyYAML 6.0.3
```

O Python existente em `.venv/` é 3.9.6. Não é necessário instalar ou atualizar dependências para usar o ambiente já preparado. Os módulos em `src/` são carregados pelo launcher; não é necessária instalação do projeto como pacote.

## Execução offline

Na raiz do repositório, definir esta função somente na sessão atual do terminal:

```sh
offline_python() {
  env -i PATH=/usr/bin:/bin \
    HOME="$PWD" TMPDIR="$PWD" \
    .venv/bin/python -I -S -B tools/offline_python.py "$@"
}
```

O launcher adiciona `src/` e o PyYAML do venv ao caminho de importação, ignora site/.pth e bloqueia eventos Python de rede/subprocessos e acesso a arquivos fora do projeto/runtime. É proteção adicional, não sandbox de sistema operacional.

### Testes e suíte histórica

```sh
offline_python tests/run_all.py
offline_python scripts/run_scenarios.py
```

Referência verificada: **47 testes aprovados** e **16/16 concordâncias com rótulos sintéticos históricos**. O termo “Acurácia” impresso pelo script histórico não significa validação científica independente.

### Visão global e seleção explícita

```sh
offline_python src/exposure_analyzer_v2.py \
  --manifests tests/fixtures/cp02.1/multi-workload.yaml \
  --mode system --format text

offline_python src/exposure_analyzer_v2.py \
  --manifests tests/fixtures/cp02.1/multi-workload.yaml \
  --mode target --target Deployment/demo/backend --format json
```

Na fixture, o global é Open e o backend selecionado é Controlled. A seleção usa exatamente `Kind/namespace/nome`; alvo inexistente ou ambíguo produz erro, sem substituição pelo máximo global. JSON versionado: `1.0.0`. Workload é uma unidade operacional provisória, não definição normativa do componente afetado no SSVC.

Snapshot sintético opcional:

```sh
offline_python src/exposure_analyzer_v2.py \
  --manifests tests/fixtures/cp02.1/multi-workload.yaml \
  --cloud tests/fixtures/cp02.1/cloud.json \
  --mode target --target Deployment/demo/frontend --format json
```

### Comparação B1 × B2

Consultar a rodada preservada em [results/cp01.2](results/cp01.2/). Para reproduzir, escolher um diretório ainda inexistente:

```sh
offline_python src/run_experiments.py --output results/meeting-01
```

B1 usa os 16 manifestos sem snapshot, mantendo suas annotations AWS. B2 usa os mesmos manifestos nos dez cenários com snapshot válido. Seis B2 são não aplicáveis. O executor exporta JSON completo, CSV pareado, resumo JSON e relatório Markdown, recusando sobrescrita de rodada existente.

| Conjunto | Concordância histórica |
|---|---:|
| B1 completo | 13/16 |
| B1 pareado | 7/10 |
| B2 pareado | 10/10 |

Houve três mudanças de categoria e dez mudanças de confiança heurística. Rótulos de mesma autoria das regras não são um gabarito científico independente. **B0 — Copilot original — permanece pendente de confirmação com Jan.**

## Dados de entrada e limites

`src/exposure_analyzer.py` mantém as regras históricas. Aceita arquivo/diretório YAML; o snapshot opcional usa `LoadBalancers`, `SecurityGroups` e `Nodes` (resumo sintético). A ligação ao LB usa hostname do status. Evidências e notas são preservadas; low/medium/high são confiança heurística legada, não probabilidades.

O máximo global não demonstra fronteira normativa de sistema. NetworkPolicy, SGs, caminhos de rede e defaults de controladores são interpretados parcialmente. Não há vínculo CVE→biblioteca/função, coleta ao vivo ou validação do enforcement. A reorganização não mudou regras ou rótulos.

`scripts/build_scenarios.py` é o gerador histórico: **remove e recria `scenarios/`**. Não faz parte do fluxo de teste/demonstração e não foi executado durante a reorganização.

## Documentação e preservação

- [Índice da documentação](docs/README.md)
- [Fundamentação científica](docs/foundation/cp01-ssvc-foundation.md)
- [Execução CP01.2](docs/checkpoints/cp01.2-execution.md)
- [Contrato e testes CP02.1](docs/checkpoints/cp02.1-unit-of-analysis.md)
- [Resumo da sessão de 26/11/2026](docs/sessions/session-summary-2026-11-26.md)
- [Organização e referências históricas dos resultados](results/README.md)

Relatórios foram mantidos com seus resultados históricos e links atualizados. Hashes, caminhos e estados de Git gravados nos JSONs/logs representam o layout da execução original, anterior à reorganização; esses artefatos não foram reescritos. O classificador histórico foi apenas movido, preservando seus bytes. Os ajustes do executor, adaptador e scripts limitam-se a caminhos de arquivos/importação.

## Restrições permanentes

Nenhum comando experimental deve consultar rede, contas, credenciais, profiles AWS, kubeconfigs ou contextos Kubernetes. Não usar AWS CLI, kubectl, Helm ou Terraform. YAMLs não são aplicados em clusters; JSONs não são coletados de serviços. A conta acadêmica futura continua sem autorização de uso. Os dois PDFs científicos permanecem locais em `references/`, ignorados pelo Git.
