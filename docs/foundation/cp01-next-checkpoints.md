# CP01.1 — Plano priorizado e encerramento

> Nota de organização: caminhos e links foram atualizados após o checkpoint. Resultados, hashes e estados de Git descritos abaixo são registros históricos da execução original. Veja o README para a estrutura atual.

Data: 26/11/2026. **Plano proposto; CP01.2 não iniciado.** Este checkpoint criou apenas os cinco documentos solicitados. Não alterou código, fixtures, rótulos, PDFs ou configurações.

## 1. Prioridades e sequência

P0 = validade científica; P1 = escopo mínimo; P2 = desejável. Complexidade relativa: baixa = mudança localizada/documental; média = vários ramos e testes; alta = interação entre modelo, corpus e observação. Não são estimativas de prazo.

| ID / prioridade | Problema e justificativa | Arquivos potencialmente afetados no futuro | Resultado esperado | Dependências | Critérios de aceitação | Complexidade |
|---|---|---|---|---|---|---|
| P0-01 | Versão e interpretação sem pin; regras não rastreáveis | `docs/foundation/cp01-*`, futuro catálogo documental de regras | Base semântica estável | Decisão de Andrey; confirmação histórica de Jan apenas para B0 | Versão de EXP, revisão da fonte, fronteira Small/Controlled e pressupostos registrados; regra própria identificada como interpretação | Baixa/média |
| P0-02 | Workload/global confundidos com componente afetado | `src/exposure_analyzer.py`, documentação, futuros testes separados | Unidade de exposição e agregação pertinentes | P0-01 e definição do contrato | Identificação explícita do alvo; exemplo multiworkload preserva diferenças; máximo global não atribuído a todo CVE | Média |
| P0-03 | Ausência de dados gera níveis reduzidos definitivos e high | `src/exposure_analyzer.py:62–110,136–156,267–275`, formato de saída | Suficiência, lacunas e fallback separados | P0-01; contrato aprovado | SG ausente/nó incompleto não prova restrição; inconclusivo não vira categoria oficial; fallback Open distinguível em JSON | Média |
| P0-04 | Small automático por netpol | `src/exposure_analyzer.py:200–219,267–271`, novos testes em corpus separado | Critério Small justificável | P0-01/P0-03 | Remover implicação automática no modelo aprovado; cenário histórico preservado; casos sem base retornam lacuna, sem novo rótulo inventado | Média |
| P0-05 | Oráculo e regras com mesma construção | Documentação metodológica e futuro corpus de avaliação separado | Protocolo anterior ao ajuste e observação independente | Alinhamento de Andrey | Critérios e denominadores congelados; famílias de desenvolvimento/avaliação separadas; desvios documentados | Média |
| P0-06 | Baseline original não disponível | Futuro adaptador B0 e documentação, sem alterar motor B1/B2 por essa dependência | Comparação fiel ou pendência declarada | Jan: código/versão/regras/licença | B0 executável e confirmado; se ausente, nenhuma aproximação chamada de original e conclusões limitadas a B1/B2 | Baixa a média, dependência externa |
| P1-01 | Correlação DNS/controlador/nós simplificada | `src/exposure_analyzer.py:52–85,128–156,173–189,240–255` | Caminhos do alvo verificáveis | P0-02/P0-03 | Ambiguidade explícita; múltiplos controladores não selecionados por primeiro resultado; nós e portas pertinentes identificados | Média/alta |
| P1-02 | Política/SG parcialmente interpretados aparentam cobertura completa | `src/exposure_analyzer.py:74–85,200–219`, documentação de capacidades | Subconjunto suportado fiel e lacunas fora dele | P0-03/P0-04 | Seletores/portas/protocolos suportados testados; semântica não suportada sinalizada; não implementar toda rede AWS para satisfazer escopo | Média/alta |
| P1-03 | Não há execução pareada nem métricas de abstinência | `scripts/run_scenarios.py` ou executor experimental novo, futuras saídas estruturadas | B1/B2 comparáveis e exportáveis | P0-03/P0-05 | Mesmo manifesto/hash; resultados brutos preservados; cobertura, direção e fallback com denominadores explícitos | Média |
| P1-04 | Evidências são strings sem ponteiro | `src/exposure_analyzer.py:104–110,272–301` e catálogo de regras | Rastreabilidade de campo e derivação | P0-02/P0-03 | Conclusão reconstruível por alvo, regra, entrada, campo, instante e faltas | Média |
| P1-05 | Regressão verifica só agregado e não sinaliza divergência no exit code | `scripts/run_scenarios.py`, futuros testes locais | Verificação significativa de comportamento | Modelo aprovado e autorização de implementação | Casos negativos detectam divergência; evidências/estado/individuais verificados; fixtures originais preservadas ou migração separada aprovada | Baixa/média |
| P1-06 | Validação operacional ainda inexistente | Plano documental futuro, corpus/observações futuros | Evidências empíricas controladas | Plano completo, custo e autorização explícita de conta pessoal | Isolamento demonstrado sem consultar configs profissionais; controles positivos/negativos; recursos removidos e resíduos verificados | Alta, autorizada separadamente |
| P2-01 | Integração não formalizada | Futuro adaptador e schema documental | Contrato para possível integração Copilot | Jan e estabilização B1/B2 | Exemplo de entrada/saída reproduzível, sem integração completa obrigatória | Média |
| P2-02 | Ambiente e uso pouco documentados | README e documentação futura | Execução offline simples | Modelo estável | Versão Python definida; comando de suíte existente separado do gerador destrutivo | Baixa |

Não é necessário reescrever o projeto: parser, `Cloud`, `Entry`, avaliadores de Service/Ingress e `analyze` podem ser evoluídos em etapas. Não implementar todos os caminhos de rede, prova de exploração, análise estática de bibliotecas, mesh ou agentes autônomos.

## 2. Checkpoints propostos

| Etapa | Conteúdo | Saída / limite |
|---|---|---|
| CP01.2 | Discussão e consolidação das decisões científicas, contrato e prioridades | Aprovação explícita antes de implementação; este documento não a concede |
| Próximo checkpoint de implementação | P0 de unidade, evidência, Small e fallback; preservar regressão histórica | Alterações pequenas com testes pertinentes, somente quando autorizadas |
| Checkpoint experimental offline | Corpus separado e execução pareada B1/B2; B0 se confirmado | Métricas e divergências sem acesso a infraestrutura |
| Checkpoint de planejamento empírico | Plano acadêmico de isolamento, recursos, custos, permissões, coleta, validação e remoção | Plano revisável; nenhum provisionamento por inferência de autorização |
| Checkpoint empírico futuro | Apenas após autorização específica da conta pessoal | Evidências e limpeza verificável; ambiente profissional permanentemente excluído |

Essa sequência é proposta de trabalho, não mudança automática do significado de futuros checkpoints do usuário.

## 3. Solicitações a Jan Filho

Nenhuma mensagem foi enviada ao autor. Lista abaixo é conteúdo a solicitar posteriormente pelo usuário ou mediante autorização explícita.

### Indispensáveis para B0 fiel

1. Código original do ponto System Exposure e commit/tag usado no artigo; dependências e comando mínimo offline.
2. Mapeamento exato das entradas para os três valores, versões CVSS aceitas, prioridade entre vetores, dados ausentes/conflitantes e defaults.
3. Versão/commit da árvore SSVC e identificação do ponto de decisão utilizado.
4. Contrato de entrada/saída e significado de “serviço”: vínculo CVE/componente/implantação, inferência inicial versus valor revisto pelo operador e persistência/reuso.
5. Permissão/licença para executar, estudar, adaptar e redistribuir o código e demonstradores, se necessários; acesso não implica permissão de redistribuição.

### Desejáveis

- Testes internos de exposição, exemplos e justificativas não publicados.
- Demonstradores e possibilidade de reutilização sem segredos/dados sensíveis.
- Formato STIX ou interface para futura integração, sem tornar integração completa requisito.
- Denominadores e filtros das matrizes técnicas: células somam 143.796, texto informa 144.163; confirmar versão do artigo/dados.
- Eventuais diferenças entre implementação do artigo e versão atual.

**Dependência delimitada:** Jan é necessário para afirmar fidelidade de B0; não bloqueia formulação, implementação autorizada ou avaliação interna B1/B2. Se B0 não for obtido a tempo, discutir com Andrey a redução explícita da comparação nas conclusões.

## 4. Decisões para Andrey

1. Adotar EXP 1.0.1 e qual revisão imutável da documentação?
2. Confirmar componente implantado como unidade principal e máximo global como resumo?
3. Aprovar retirada da implicação automática NetworkPolicy→Small e critérios de evidência mínima?
4. Aprovar saída inconclusiva com fallback Open separado, sem quarta categoria oficial?
5. Definir conclusão sobre configuração declarada em B1 versus exposição operacional e eventuais metadados contextuais comuns.
6. Aprovar protocolo sem participantes humanos, com oráculo normativo prévio e observações controladas futuras?
7. Qual mínimo de diversidade de famílias e evidência empírica é viável para o TCC?
8. Como tratar indisponibilidade de B0 e possibilidade de reutilização dos demonstradores?
9. Confirmar escopo mínimo e exclusões, sem expansão para mesh/AI-SSVC/LLMs?

Essas questões exigem alinhamento científico; não são pedidos para autorizar infraestrutura agora.

## 5. Registro de integridade e estado Git

Estado inicial verificado: branch `main`, HEAD `b62d233`, arquivos rastreados sem alterações; dois PDFs não rastreados já presentes. Não houve fetch, stage, commit, push ou mudança de configuração Git.

Arquivos documentais novos:

- `docs/foundation/cp01-ssvc-foundation.md`
- `docs/foundation/cp01-rule-traceability.md`
- `docs/foundation/cp01-design-decisions.md`
- `docs/foundation/cp01-experimental-methodology.md`
- `docs/foundation/cp01-next-checkpoints.md`

Estado final esperado e verificado no encerramento: apenas os cinco documentos novos e os dois PDFs previamente não rastreados; nenhum arquivo rastreado modificado. PDFs continuam fora do índice. A suíte existente reproduziu 16/16 com Python 3.9.6 e PyYAML 6.0.3, tempo real 0,06 s; não houve instalação nem execução do gerador. Extração/renderização de leitura usou PDFKit local, com artefatos temporários fora do repositório.

Restrições preservadas: nenhuma consulta ou alteração a credenciais, profiles AWS, kubeconfigs, contextos Kubernetes ou infraestrutura profissional; nenhuma AWS CLI/API, kubectl, Terraform, varredura ou provisionamento. Conta acadêmica futura não autorizada; isolamento profissional é permanente.

**Encerramento:** aguardar aprovação explícita para CP01.2. Nenhuma alteração proposta neste conjunto está implementada.
