# Encerramento da sessão — 26/11/2026

> Nota de organização: caminhos e links foram atualizados após o checkpoint. Resultados, hashes e estados de Git descritos abaixo são registros históricos da execução original. Veja o README para a estrutura atual.

Projeto: classificação determinística de System Exposure do SSVC com dados Kubernetes/AWS. Último checkpoint concluído: **CP02.1**. Nenhum checkpoint posterior foi iniciado ou autorizado. Data no fuso America/Fortaleza.

## 1. Estado atual do protótipo

O protótipo está funcional para análise **offline de arquivos locais e sintéticos**, com Python 3.9.6 e PyYAML 6.0.3 no ambiente virtual existente. A implementação histórica foi preservada; uma camada nova permite escolher explicitamente um workload sem substituir sua classificação pelo máximo global.

O desenvolvimento desta sessão não demonstra validação científica definitiva das categorias. A seleção de workload é uma decisão operacional provisória, não uma definição normativa estabelecida pelo SSVC.

| Componente | Funcionalidade implementada | Referência |
|---|---|---|
| Classificador histórico | YAML Kubernetes, JSON sintético AWS opcional, exposição por workload, evidências textuais, confiança heurística e máximo global | [`src/exposure_analyzer.py`](../../src/exposure_analyzer.py) |
| Suíte histórica | Verificação dos 16 cenários e rótulos originais | [`scripts/run_scenarios.py`](../../scripts/run_scenarios.py) |
| Executor experimental | B1/B2 separados, elegibilidade, hashes, resultados completos, comparação pareada, métricas e exportação sem sobrescrita silenciosa | [`src/run_experiments.py`](../../src/run_experiments.py) |
| Camada CP02.1 | Modos system/target; identidade Kind/namespace/nome; contexto global; erros estruturados; JSON 1.0.0 e texto | [`src/exposure_analyzer_v2.py`](../../src/exposure_analyzer_v2.py) |
| Launcher local | Inicialização sem site/.pth, ambiente limpo nos comandos e bloqueios de auditoria Python para rede/subprocessos/arquivos | [`tools/offline_python.py`](../../tools/offline_python.py) |

Não foram implementadas regras de exposição revisadas, evidências estruturadas do CP02.2, coleta real, associação CVE→componente ou integração com Copilot. B0 continua pendente.

## 2. Resultados experimentais e testes

### Referência sintética histórica

A suíte original permaneceu em **16/16 concordâncias**, antes e depois do CP02.1. Distribuição: Small=1, Controlled=9, Open=6; nenhuma subestimativa ou superestimativa relativa aos rótulos históricos. Os logs antes/depois são idênticos.

### Comparação preliminar B1 × B2

| Configuração/conjunto | N executado | Small / Controlled / Open | Concordância histórica | Subestimativas | Superestimativas |
|---|---:|---|---|---|---|
| B1 completo | 16 | 1 / 8 / 7 | 13/16 = 81,25% | 1/16 | 2/16 |
| B1 pareado | 10 | 0 / 4 / 6 | 7/10 = 70% | 1/10 | 2/10 |
| B2 pareado | 10 | 0 / 5 / 5 | 10/10 = 100% | 0/10 | 0/10 |

Foram encontrados dez snapshots sintéticos válidos para o subconjunto estrutural aceito. Seis casos B2 são não aplicáveis por ausência de snapshot. Nenhum erro na rodada experimental oficial. B1 mantém annotations AWS dos manifestos; B2 acrescenta somente o snapshot correspondente.

Nos dez pares, houve **três mudanças de categoria**: cenário 07 Controlled→Open; 13 e 15 Open→Controlled. Os outros sete mantiveram a categoria. A confiança heurística mudou nos dez pares; em sete, foi a única mudança de categoria/confiança, embora as evidências textuais também tenham mudado.

A comparação com denominador comum é **7/10 versus 10/10**, sem usar B2 como gabarito. Esses valores são **concordância com rótulos sintéticos históricos**, não acurácia científica ou prova de superioridade de B2. Rótulos e fixtures têm autoria vinculada ao desenvolvimento das regras.

Dados preservados: [resumo JSON](../../results/cp01.2/summary.json), [outputs completos](../../results/cp01.2/raw_results.json), [pares CSV](../../results/cp01.2/paired_comparison.csv) e [relatório descritivo](../../results/cp01.2/report.md).

### Seleção explícita CP02.1

Na fixture multiworkload, o contexto global é Open. Selecionar backend retorna Controlled; selecionar worker retorna Small pelas regras legadas. O alvo inexistente retorna seleção nula e erro, mantendo Open apenas como contexto global. Duplicatas são rejeitadas, sem escolha arbitrária.

**Testes aprovados:** 26 novos de seleção/agregação, em 0,150 s; 21 existentes do executor, em 0,127 s na verificação final. Total: **47 testes distintos**, além da suíte de 16 cenários. O teste de preservação da camada nova compara resultados integrais em 26 combinações históricas de entrada: 16 sem snapshot e dez com snapshot; não são 26 cenários independentes.

Evidências: [testes novos](../../results/cp02.1-validation/new-tests.txt), [testes existentes](../../results/cp02.1-validation/existing-tests-after.txt), [suíte histórica](../../results/cp02.1-validation/historical-after.txt). Tempos são observações locais, não benchmark estatístico.

## 3. Roteiro para demonstração em reunião

Executar a partir da raiz `/Users/andrezavilar/exposicao-sistema-ssvc`. Não é necessário instalar dependências ou ativar o venv: os comandos apontam diretamente para ele.

Definir esta função apenas na sessão atual do terminal; ela não altera arquivos de configuração:

```sh
offline_python() {
  env -i PATH=/usr/bin:/bin \
    HOME=/Users/andrezavilar/exposicao-sistema-ssvc \
    TMPDIR=/Users/andrezavilar/exposicao-sistema-ssvc \
    .venv/bin/python -I -S -B tools/offline_python.py "$@"
}
```

### 3.1. Mostrar os 16 resultados históricos

```sh
offline_python scripts/run_scenarios.py
```

Resultado verificado: 16/16. O script histórico imprime a palavra “Acurácia”; durante a apresentação, explicar que significa concordância com rótulos sintéticos históricos, sem validação independente.

### 3.2. Mostrar o contexto global e selecionar o backend

```sh
offline_python src/exposure_analyzer_v2.py \
  --manifests tests/fixtures/cp02.1/multi-workload.yaml \
  --mode system --format text

offline_python src/exposure_analyzer_v2.py \
  --manifests tests/fixtures/cp02.1/multi-workload.yaml \
  --mode target --target Deployment/demo/backend --format text
```

Resultados verificados: global Open; backend Controlled com global Open disponível como contexto. A segunda execução mostra por que a classificação do conjunto não deve ser aplicada automaticamente a cada componente.

### 3.3. Mostrar seleção Small e snapshot opcional

```sh
offline_python src/exposure_analyzer_v2.py \
  --manifests tests/fixtures/cp02.1/multi-workload.yaml \
  --mode target --target Deployment/demo/worker --format json

offline_python src/exposure_analyzer_v2.py \
  --manifests tests/fixtures/cp02.1/multi-workload.yaml \
  --cloud tests/fixtures/cp02.1/cloud.json \
  --mode target --target Deployment/demo/frontend --format json
```

Worker retorna Small segundo o legado, condição coberta pelos testes; isso não valida a equivalência NetworkPolicy→Small. Frontend com snapshot sintético retorna Open/high; high continua sendo confiança heurística legada, não probabilidade.

### 3.4. Mostrar erro sem classificação substituta

```sh
offline_python src/exposure_analyzer_v2.py \
  --manifests tests/fixtures/cp02.1/multi-workload.yaml \
  --mode target --target Deployment/demo/missing --format json
```

Resultado verificado: `status=error`, `selected_exposure=null`, `global_exposure=open`, erro `target_not_found` e código de saída 1. Esse erro é intencional na demonstração.

### 3.5. Demonstrar o experimento e os testes

Para mostrar a rodada já realizada, abrir os arquivos de `results/cp01.2/`. Para uma nova execução, escolher **outro diretório ainda inexistente**:

```sh
offline_python src/run_experiments.py --output results/cp01.2-meeting-01
```

Esse comando é um roteiro para a reunião, **não foi executado no encerramento**. Cria arquivos locais de uma nova rodada. Se o diretório já existir, o executor recusa a gravação; escolher outro nome, sem apagar a referência anterior. Não executar o gerador `scripts/build_scenarios.py`.

Testes reproduzíveis:

```sh
offline_python tests/test_exposure_analyzer_v2.py
offline_python tests/test_run_experiments.py
```

Nenhum comando acima aplica manifestos ou consulta serviços externos. Para uma demonstração curta, bastam a suíte histórica, a comparação system/target e o erro de alvo inexistente.

## 4. Limitações técnicas e metodológicas

- Workload é aproximação operacional; não há vínculo explícito de vulnerabilidade com biblioteca, função, container ou interface afetada.
- O máximo global resume os workloads carregados, sem demonstrar fronteira completa de sistema/aplicação.
- As regras históricas permanecem heurísticas. NetworkPolicy, SGs, defaults de controladores e caminhos de rede são interpretados parcialmente; completude e enforcement não são verificados.
- A confiança low/medium/high não é calibrada. A camada de seleção não inventa confiança global ou novos indicadores de suficiência.
- Evidências continuam textuais; não foi implementado o modelo de evidências previsto para CP02.2.
- Identidades duplicadas invalidam o conjunto, mesmo se o alvo escolhido for outra identidade. Não há consolidação por ownerReferences.
- Corpus pequeno e sintético, sem referência científica independente, validação empírica ou estudo de generalização. A permanência em 16/16 não prova validade das regras.
- Não há resultado de B0 nem comparação com o código original confirmado do Copilot.
- A sandbox adicional de SO foi recusada no CP01.2. Ambiente limpo e audit hooks são proteção adicional, não isolamento por kernel nem barreira contra código nativo malicioso.

## 5. Decisões para discutir com Andrey

1. Qual unidade científica será adotada: componente implantado, workload ou outra granularidade? Como informar o vínculo com a vulnerabilidade?
2. Quando o máximo global é um resumo adequado e qual fronteira de aplicação deve ser explícita?
3. Qual versão/revisão normativa será congelada e quais condições justificam Small ou Controlled?
4. Como separar resultado sustentado, inferência, dados incompletos, contradições e fallback conservador, sem criar novas categorias oficiais?
5. Qual protocolo de validação normativa, sintética e empírica será aprovado, com referência definida antes do ajuste e sem dependência contínua de especialistas?
6. Qual diversidade mínima de topologias e componentes é viável para o TCC? Como relatar ausência de B0, se necessário?
7. Manter a rejeição integral de duplicatas e a interpretação provisória de workload?

As propostas do CP01.1 continuam sujeitas a alinhamento científico. A autorização técnica dos checkpoints executados não implica aprovação científica de todas as interpretações.

## 6. Dependências de colaboração com Jan

Para reproduzir B0 fielmente, solicitar código/commit usado no artigo, dependências, comando mínimo, regras exatas de exposição, versões CVSS aceitas e tratamento de dados ausentes/conflitantes. Confirmar a árvore/versão SSVC, contratos de entrada/saída, identidade de serviço/componente, diferença entre inferência inicial e revisão pelo operador e persistência/reuso.

Também esclarecer licença/permissões de execução, adaptação e eventual distribuição. Como informações desejáveis: testes internos, demonstradores reutilizáveis e possibilidades de integração. Confirmar denominadores das matrizes do artigo, cuja soma das células difere do total textual informado, conforme [fundamentação CP01.1](../foundation/cp01-ssvc-foundation.md#22-avaliação-apresentada-e-alcance-dos-resultados).

Nenhuma mensagem foi enviada a Jan. Sua colaboração é indispensável para afirmar fidelidade de B0, mas não bloqueia trabalho B1/B2 devidamente autorizado. Não implementar aproximação e chamá-la de Copilot original.

## 7. Próximos passos recomendados — não executados

1. Apresentar os resultados e decisões pendentes ao orientador e obter autorização para o próximo checkpoint.
2. Após autorização específica, tratar evidências estruturadas, identidade/proveniência e incerteza, preservando compatibilidade e referências históricas.
3. Revisar regras somente em checkpoint próprio, especialmente a produção automática de Small e conclusões reduzidas por ausência de informação.
4. Formalizar corpus independente do ajuste, critérios normativos e métricas com denominadores explícitos.
5. Obter ou confirmar B0 com Jan; manter comparação original pendente até isso ocorrer.
6. Antes de qualquer experimento real futuro, apresentar plano de isolamento acadêmico, recursos mínimos, estimativa de custos, permissões mínimas, coleta, critérios de validação e remoção dos recursos. A conta pessoal ainda não está autorizada.

Não se iniciou CP02.2, revisão de regras, coleta real, provisionamento ou integração adicional.

## 8. Estado final dos arquivos e do Git

Branch: `main`; HEAD observado: `ed6cc62`, mensagem `docs(experiments): relata execução e limitações do CP01.2`. Referência local `origin/main` sem divergência indicada; nenhum fetch foi realizado, portanto não há afirmação sobre o remoto atualizado.

Os quatro commits CP01 constam no histórico, realizados pelo usuário antes do CP02.1. O agente não criou commits nem realizou push. Não há alterações em arquivos rastreados ou staged.

Novos arquivos CP02.1, ainda não rastreados:

- `src/exposure_analyzer_v2.py`.
- `tests/test_exposure_analyzer_v2.py`.
- `tests/fixtures/cp02.1/multi-workload.yaml` e `cloud.json`.
- `docs/checkpoints/cp02.1-unit-of-analysis.md`.
- `results/cp02.1-validation/`: logs, quatro exemplos JSON e hashes antes/depois.
- Este resumo `docs/sessions/session-summary-2026-11-26.md`.

Os PDFs locais em `references/` permanecem não rastreados e não devem ser incluídos nos commits. `.venv/` não deve ser versionado.

Os **68 arquivos preexistentes** da verificação CP02.1 mantiveram seus hashes, incluindo código, testes históricos, cenários, resultados CP01.2, documentos e PDFs. Evidência: [antes](../../results/cp02.1-validation/protected-before.sha256) e [depois](../../results/cp02.1-validation/protected-after.sha256).

No encerramento, o único arquivo criado adicionalmente foi este resumo. Código e fixtures não foram alterados desde os testes aprovados; não foi necessária repetição de testes para uma adição exclusivamente documental.

## 9. Segurança e encerramento

Nenhuma configuração, credencial, profile ou contexto corporativo foi consultado, listado ou alterado. Não foram usados AWS CLI, SDK cloud, APIs AWS/Kubernetes, kubectl, Helm, Terraform, sudo ou infraestrutura profissional. Não houve instalação, conexão de rede experimental, varredura, exploração ou provisionamento.

Todos os dados e temporários experimentais permaneceram no projeto. As restrições sobre o ambiente profissional são permanentes; autorização futura da conta pessoal não as modifica. A conta acadêmica pessoal continua não autorizada.

Relatório técnico completo de CP02.1: [unidade de análise e seleção](../checkpoints/cp02.1-unit-of-analysis.md). Relatório experimental: [CP01.2](../checkpoints/cp01.2-execution.md). Fundamentação e planos: [CP01.1](../foundation/cp01-ssvc-foundation.md).

**Sessão encerrada após a entrega deste resumo. Nenhum novo checkpoint autorizado ou iniciado.**
