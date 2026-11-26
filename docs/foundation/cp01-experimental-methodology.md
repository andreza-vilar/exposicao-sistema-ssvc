# CP01.1 — Proposta de metodologia experimental

> Nota de organização: caminhos e links foram atualizados após o checkpoint. Resultados, hashes e estados de Git descritos abaixo são registros históricos da execução original. Veja o README para a estrutura atual.

Data: 26/11/2026. **Proposta ainda não aprovada pelo orientador. Nenhum cenário novo, coleta ao vivo ou experimento em infraestrutura foi executado.** Execução realizada neste checkpoint limita-se à suíte sintética existente, registrada na [fundamentação, seção 7](cp01-ssvc-foundation.md#7-evidência-operacional-complementar).

## 1. Pergunta, hipóteses e unidades

Investigar a contribuição de evidências operacionais para exposição do componente implantado, separando (a) comparação com Copilot original e (b) contribuição incremental AWS. Fundamentação e hipótese principal: [documento científico, seção 5](cp01-ssvc-foundation.md#5-delimitação-da-contribuição-científica-proposta).

**H1 proposta:** B2 pode resolver ambiguidades de B1 e reduzir fallback conservador sem elevar subestimativas no corpus controlado. **H0 operacional:** não há melhora observável nas medidas predefinidas; apresentar também pioras, inconclusivos e casos sem mudança. Hipótese não é resultado.

Unidade de medição: componente afetado + implantação + instante + caminhos pertinentes. Unidade de pareamento B1/B2: mesmo cenário/componente. Repetições da mesma análise determinística não são novas amostras independentes. Variantes de uma mesma topologia devem ser agrupadas por família na análise.

## 2. Configurações

| Configuração | Entradas e comportamento | Estado atual / restrição |
|---|---|---|
| B0 — original | Implementação e versão originais confirmadas por Jan, incluindo regras reais de exposição e modos de revisão | Código indisponível localmente; nenhuma aproximação implementada |
| B1 — Kubernetes-only | Manifestos do cenário, sem snapshot AWS; annotations AWS permitidas e explicitadas; metadados mínimos de alvo/fronteira | Modo sem `--cloud` existe (`src/exposure_analyzer.py:293–301`); semântica revisada ainda proposta |
| B2 — Kubernetes + AWS | Exatamente os manifestos de B1, mais snapshot AWS correspondente; mesmo motor, regras e contexto comum | Modo com `--cloud` existe; suficiência/correlação revisadas ainda propostas |

O corpus atual executa uma mistura de modos conforme existência de `cloud.json`, não um experimento pareado (`scripts/run_scenarios.py:10–13`). A suíte 16/16 não é um resultado comparativo B0/B1/B2.

**B0 e interação humana:** a publicação permite revisão/reuso por operador (artigo p. 8, §5.2). Propor como comparação primária a inferência automática inicial confirmada. Não comparar B1/B2 automáticos a B0 corrigido manualmente sem relatar essa diferença. Caso o modo automático original não possa ser isolado, registrar limitação e avaliar a comparabilidade antes de executar. Sem B0 confirmado, publicar apenas comparação B1/B2 e dependência pendente.

**Contexto adicional:** identificação do componente é comum. Dados como Automatable, uso de função vulnerável e perfis de rede não podem entrar silenciosamente só em B2. Se necessários aos critérios Small, fornecê-los de forma independente e idêntica ou declarar a classificação inconclusiva. Esse desenho deve ser aprovado antes da coleta.

## 3. Variáveis e controles

| Tipo | Definição proposta |
|---|---|
| Independente principal | Fonte de evidência: manifestos versus manifestos + AWS, em B1/B2 |
| Independente de comparação | Método original B0 versus modelo proposto, com contratos e diferenças de entrada declarados |
| Fatores planejados | Tipo de entrada, fronteira pública/privada, restrição de origem, múltiplos caminhos, completude, divergência, componente alvo |
| Dependentes | Categoria, estado determinado/inconclusivo, fallback, direção de divergência, lacunas, rastreabilidade e tempo |
| Constantes B1/B2 | Componente e CVE quando aplicável, manifestos byte a byte, contexto comum, versão das regras, ambiente Python, semântica SSVC, fronteira, instante lógico |
| Constantes do cenário | Oráculo, fontes de referência, procedimentos de observação e critérios de sucesso definidos antes de ver a saída |

Snapshots devem representar o mesmo instante lógico dos manifestos. Variantes para ausência/contradição de dados serão planejadas em corpus futuro, identificadas separadamente; não apagar campos das fixtures atuais neste checkpoint.

## 4. Validação em camadas

### 4.1. Fundamentação normativa

Congelar versão e interpretação da fonte, tabela de critérios, pressupostos e critérios de suficiência antes de ajustar o motor. Para cada caso futuro, registrar qual premissa normativa é exercitada e qual evidência pode refutá-la. Revisão de Andrey em marcos substitui participação contínua, mas não transforma autoria própria em validação independente.

### 4.2. Testes de implementação

Preservar os 16 casos atuais como regressão histórica. Em etapa autorizada, acrescentar testes de parsing, seleção, correlação e agregação com expectativas justificadas. Verificar categoria individual, evidências e fallback, além do máximo. Testes que espelham ramificações mostram consistência, não demonstram validade das premissas científicas.

### 4.3. Cenários sintéticos independentes do ajuste

Proposta: separar corpus de desenvolvimento e corpus de avaliação por família de topologia; fixar expectativas de avaliação antes de observar resultados do classificador revisado. A mesma pesquisadora poderá definir os casos a partir de protocolo publicado, mas deve reconhecer a dependência de autoria. Guardar histórico de decisões e não alterar rótulos para elevar métricas.

O oráculo deve conter: componente, fronteira, fontes normativas, evidências exigidas, premissas, categoria quando justificável e status indeterminado quando faltar base. Uma configuração sintética não comprova que um controle funciona em implantação real. Não usar o output B2 como gabarito de B1.

### 4.4. Observações controladas futuras

Somente após autorização específica e plano de isolamento: usar aplicação de demonstração não vulnerável e verificações benignas de conectividade entre origens previamente definidas, com logs/configurações coletados separadamente da saída do classificador. Não executar exploits, scanners externos ou testes contra sistemas profissionais.

Origens de teste propostas: cliente acadêmico externo autorizado, origem interna permitida e origem interna não permitida, conforme cenário. Observar porta/interface do componente, em vez de apenas saúde do LB. Registrar tentativas positivas e negativas, saúde da aplicação e instante. Uma falha de conexão isolada pode ser indisponibilidade, não prova de isolamento; controles positivos devem distinguir esses casos.

Observações não fornecem categoria SSVC sozinhas: são combinadas a critérios normativos previamente fixados. Small exige argumento próprio; um único teste de bloqueio não demonstra rede altamente controlada. Se esse argumento não puder ser sustentado, o oráculo também pode permanecer indeterminado.

## 5. Métricas e denominadores

Definir `N` como número de unidades elegíveis, `N_ref` como unidades com categoria de referência justificada e `N_det` como unidades em que o método produziu categoria sustentada. Publicar exclusões e interseções, sem trocar denominadores entre métodos.

Ordem ordinal para análise de direção: Small=0, Controlled=1, Open=2. Essa codificação é uma convenção analítica, não escala métrica de risco.

| Medida | Definição / cuidado |
|---|---|
| Cobertura determinada | `N_det / N`, por método e família |
| Inconclusivos | quantidade e proporção, com motivos e referência disponível ou não |
| Fallback | frequência sobre N; separar de Open sustentado |
| Concordância condicionada | acertos entre casos com referência e previsão sustentada, dividido por esse subconjunto; sempre acompanhado da cobertura |
| Resolução correta total | previsões sustentadas concordantes divididas por `N_ref`; evita premiar abstinência sem mostrar perdas |
| Subestimativa | previsão sustentada abaixo da referência; informar número, taxa sobre N_ref e denominador condicionado |
| Superestimativa | previsão sustentada acima da referência; mesmos denominadores explícitos |
| Matriz | linhas da referência; colunas Small/Controlled/Open e coluna de inconclusivo; fallback em tabela operacional separada |
| Distância ordinal | diferença de 1 ou 2 níveis; se usada média absoluta, esclarecer que não mede magnitude de risco |
| Rastreabilidade | fração de conclusões com regra, origem, campo, alvo e lacunas identificáveis; avalia explicabilidade documental |
| Custo local | tempo real e ambiente; repetições para ruído temporal, sem tratá-las como novas topologias |

Não contar fallback Open como acerto de categoria sustentada, mesmo quando coincide com referência Open. Avaliar também a decisão operacional separadamente, deixando claro que ela inclui política conservadora.

### 5.1. Comparação incremental

Produzir tabela pareada B1→B2: sem mudança; inconclusivo resolvido corretamente/incorretamente; erro corrigido; novo erro; conflito revelado; perda de determinação. Publicar transições e exemplos divergentes, não apenas média agregada. Ganho pode ser maior suficiência sem mudança de categoria.

B0 deve usar as mesmas unidades elegíveis e referência independente. Se não aceitar determinado cenário ou componente, informar não aplicabilidade; não inventar um resultado. Comparação de desacordo B0/B2 sem oráculo não é acurácia.

Com corpus pequeno e planejado, priorizar análise descritiva e qualitativa. Intervalos ou testes estatísticos só são adequados se houver plano amostral e dependências explicitadas; múltiplas variantes da mesma aplicação não justificam generalização para toda AWS/Kubernetes.

## 6. Protocolo reproduzível proposto

1. Congelar fontes, hipóteses, unidades, configuração do modelo e regras de elegibilidade.
2. Definir corpus e oráculo antes do ajuste final, com IDs e famílias.
3. Congelar hashes de manifestos, snapshots, observações e versões.
4. Verificar integridade e completude, preservando casos inválidos como exclusões justificadas.
5. Executar B1/B2 pareados, e B0 apenas quando confirmado; guardar JSON bruto.
6. Derivar métricas em procedimento separado do classificador; registrar denominadores.
7. Analisar toda subestimativa e casos contraditórios/inconclusivos; não selecionar apenas exemplos favoráveis.
8. Relatar resultados negativos, limites e desvios do protocolo.

Metadados mínimos futuros: cenário, componente, família, B0/B1/B2, versões/hash das regras e entradas, fonte normativa, instante, observações independentes, categoria de referência, estado e resultado do método. É proposta de exportação, não formato já implementado (`src/exposure_analyzer.py:272–301`).

## 7. Ameaças à validade e mitigação

| Dimensão | Ameaça | Mitigação proposta / limite remanescente |
|---|---|---|
| Construto | Confundir acesso ao LB, ao serviço e à interface vulnerável | Fixar componente e caminho; não alegar exploração |
| Construto | Equivaler política declarada a controle efetivo | Separar modos declarado/operacional e exigir observações pertinentes |
| Interna | Rótulos moldados pelas regras | Oráculo prévio, trilha de justificativas, corpus separado; mesma autoria continua limitação |
| Interna | Diferenças extras entre B1/B2 | Mesmos manifestos/motor/contexto, variar só snapshot |
| Interna | Estado temporal divergente | Janela de coleta e hashes; invalidar pares incompatíveis |
| Comparação | B0 aproximado ou corrigido manualmente | Confirmar código/modo; separar revisão humana |
| Externa | Poucos serviços, um provedor e topologias sintéticas | Restringir conclusões ao corpus e versões avaliadas |
| Conclusão | 100% em corpus conhecido | Mostrar cobertura, diversidade e independência limitada |
| Conclusão | Desbalanceamento e muitos inconclusivos | Métricas por classe/família e denominadores completos |
| Reprodutibilidade | Defaults de controlador e fontes vivas mudam | Fixar revisão de documentação e versão de software |
| Observação | Bloqueio causado por falha da aplicação | Controles positivos, logs e repetição controlada, sem exploração |

## 8. Porta de autorização do ambiente acadêmico

Não há autorização atual para conta pessoal ou qualquer infraestrutura. Antes da fase empírica, apresentar **plano concreto** com:

- Execução separada, sem configurações corporativas montadas ou herdadas; credenciais e kubeconfig exclusivamente acadêmicos.
- Lista mínima de recursos e justificativa de cada um; comparar alternativa de laboratório local quando suficiente.
- Estimativa de custos por região, duração e componentes, com teto aprovado, fontes de preço e data. Nenhum valor foi estimado neste checkpoint porque a topologia ainda não foi escolhida.
- Permissões mínimas separadas para provisionamento, coleta e remoção; evitar acesso administrativo genérico.
- Coleta, anonimização e armazenamento de evidências sem segredos.
- Critérios de validação e de interrupção por custo ou falha de isolamento.
- Inventário dos recursos criados, procedimento de remoção e verificação posterior de resíduos/cobrança.

Somente aprovação explícita futura permite executar esse plano. O ambiente corporativo permanece fora de qualquer autorização, inclusive futura.
