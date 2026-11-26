# CP01.1 — Rastreabilidade e revisão das 20 regras

Data: 26/11/2026. Base: HEAD `b62d233e9a77a975d881b900c65212dea85bf7f9`. Documento analítico; **nenhuma regra ou fixture foi alterada**.

## 1. Convenções e âncoras

R01–R20 preservam os IDs atribuídos no CP00; não são identificadores existentes no código nem regras publicadas pelo CERT/CC. Linhas referem-se a `exposure_analyzer.py` nessa revisão. `high/medium/low` descrevem o comportamento atual, não validação de sua qualidade.

Referências científicas completas, versões e data de consulta: [fundamentação, seção 6](cp01-ssvc-foundation.md#6-referências-e-registro-de-consulta).

| Âncora | Origem oficial | Interpretação proposta pelo TCC |
|---|---|---|
| N-O | S1, Open | Demonstrar caminho relevante amplamente acessível ao componente |
| N-C | S1, Controlled; S3, mitigação | Demonstrar restrição efetiva no caminho; não inferi-la da ausência de dados |
| N-S | S1, Small; S2, heurísticas ordenadas | Exigir argumentos adicionais sobre controle elevado ou caráter local/inalcançável |
| N-U | S1/S2, default desconhecido | Registrar incerteza separadamente; Open pode ser fallback operacional |
| N-I | S2, sistema concreto; S3/S13, instância e inventário | Correlacionar componente, implantação e caminhos antes de agregar |

As interpretações da terceira coluna são critérios de projeto propostos, não equivalências Kubernetes/AWS normativas.

## 2. Inventário: comportamento atual e evidências

As justificativas gerais do protótipo estão no [README, linhas 18–24](../README.md#regras-hipótese-de-trabalho-a-validar-com-orientador). A tabela separa mecanismo atual da avaliação científica da seção 3.

| ID / fonte de código | Condição e categoria atual | Evidência e pressuposto atual | Cenários associados no executor atual |
|---|---|---|---|
| R01 — [linhas 88–92](../exposure_analyzer.py#L88) | LB `Scheme=internal` → controlled; chamador high | Snapshot/DNS correto; internal basta para resumir exposição | 05 |
| R02 — [93–95](../exposure_analyzer.py#L93) | LB não internal sem SG → open; chamador high | Lista SG vazia significa ausência real de filtro; scheme diferente/ausente segue mesmo ramo | Nenhum explícito |
| R03 — [96–99](../exposure_analyzer.py#L96) | SG com CIDR universal e sobreposição de portas → open; high | LB/snapshot correlacionados; permissão representa caminho acessível | 04, 07, 09, 11 |
| R04 — [96–100](../exposure_analyzer.py#L96) | SG sem universal encontrado → controlled; high | Dados completos; CIDR não universal é restrição relevante | 06 |
| R05 — [120–142](../exposure_analyzer.py#L120) | Service LB sem nuvem correspondente, interno por annotation/classe/default → controlled/medium | Controlador identificado e default aplicável | 16; 05 usa nuvem no executor |
| R06 — [126–142](../exposure_analyzer.py#L126) | Service LB sem nuvem, source ranges restritos → controlled/medium | Annotation/spec aplicada e não contornada | Nenhum isolado; 06/07 possuem nuvem |
| R07 — [130–142](../exposure_analyzer.py#L130) | Demais Service LB sem nuvem → open/medium | Configuração é indício de exposição pública | 08 |
| R08 — [143–148](../exposure_analyzer.py#L143) | NodePort sem nós → open/low | Desconhecido substituído por pior caso | Nenhum na suíte padrão |
| R09 — [149–152](../exposure_analyzer.py#L149) | Nós sem `PublicIpAddress` → controlled/high | Lista completa; campo ausente significa nó privado | 13 |
| R10 — [153–156](../exposure_analyzer.py#L153) | Nó público e SG universal na porta/faixa → open/high | Nó pertence ao ambiente do workload; porta roteia ao componente | 14 |
| R11 — [153–156](../exposure_analyzer.py#L153) | Nó público sem universal encontrado → controlled/high | Lista de SGs e regras suficiente | 15 |
| R12 — [169–177](../exposure_analyzer.py#L169) | ALB correlacionado → delega R01–R04; high | DNS correto; portas relevantes 80/443 | 09 |
| R13 — [170–180](../exposure_analyzer.py#L170) | ALB sem nuvem; interno ou inbound-cidrs restritos → controlled/medium | Default interno válido; configuração efetiva | 10 |
| R14 — [178–180](../exposure_analyzer.py#L178) | Demais ALB sem nuvem → open/medium | Publicação inferida das annotations | Nenhum isolado |
| R15 — [181–187](../exposure_analyzer.py#L181) | Ingress não ALB sem Service nginx → open/low | Controlador desconhecido substituído por pior caso | Nenhum |
| R16 — [182–189](../exposure_analyzer.py#L182) | Ingress herda nível/confiança do Service nginx | Primeiro Service com label nginx representa o controlador correto | 11 |
| R17 — [190–196](../exposure_analyzer.py#L190) | Allowlist nginx restrita reduz open para controlled; mantém confiança | Controlador aplica annotation à rota; não há bypass | 12 |
| R18 — [267–271](../exposure_analyzer.py#L267) | Sem entrada externa reconhecida + netpol restrictive → small/high | Inventário completo, política efetiva e suficiente para Small | 01 |
| R19 — [267–271](../exposure_analyzer.py#L267) | Sem entrada externa + netpol permissive → controlled/high | Ausência de publicação identificada afasta Open | 03 |
| R20 — [267–271](../exposure_analyzer.py#L267) | Sem entrada externa + nenhuma netpol → controlled/medium | Topologia não publicada no YAML é suficientemente restrita | 02 |

Os chamadores atribuem high para LB encontrado em `service_entry:136–140` e `ingress_entry:175–177`. R12 é delegação, não uma definição independente de exposição.

## 3. Matriz de rastreabilidade e recomendações

Cada recomendação é uma **proposta**, não alteração aplicada. “Revisar” preserva o mecanismo útil, mas rejeita sua suficiência universal. Nenhuma regra possui correspondência oficial específica do tipo “AWS/Kubernetes X implica categoria Y”.

| ID | Âncora / fundamento disponível | Limitação principal | Recomendação e justificativa |
|---|---|---|---|
| R01 | N-C/N-I; contexto privado pode restringir | Internal não exclui outro caminho nem rede interna amplamente acessível | **Revisar**: usar como evidência de caminho privado, exigir fronteira e demais entradas |
| R02 | N-O/N-U | Ausência de SG pode ser informação ausente; não comprova listener ou caminho | **Revisar**: separar observação completa de ausência documental e fallback |
| R03 | N-O; S11 apoia interpretação de SG | Protocolo, listener, targets e interface vulnerável não confirmados; CIDR literal | **Revisar**: manter detecção de permissão ampla, condicionar conclusão ao caminho correlacionado |
| R04 | N-C | SG desconhecido vira conjunto vazio; prefix lists/referências a SG e cobertura combinada de CIDRs ignorados | **Revisar**: falha de completude não pode demonstrar restrição |
| R05 | N-C; S12 documenta defaults por controlador | Versão/controlador não confirmados; falta observação | **Revisar**: registrar inferência condicionada e suficiência para configuração declarada |
| R06 | N-C; S10 como mecanismo de Service | Source ranges declarados não provam aplicação | **Revisar**: diferenciar intenção e efetividade |
| R07 | N-O/N-U | `LoadBalancer` não garante publicação nem funcionamento | **Revisar**: candidato Open declarado ou fallback, explicitando qual |
| R08 | N-U | Não há prova de abertura, apenas desconhecimento | **Manter como fallback**, removendo interpretação de Open observado; metadados necessários |
| R09 | N-C/N-I | IPv6/outros ingressos ausentes; nós não vinculados; falta campo≠fato negativo | **Revisar**: ausência de IP só é evidência quando inventário/campo têm semântica de completude |
| R10 | N-O/N-I | SGs unidos entre todos os nós; NodePort faltante usa faixa inteira | **Revisar**: manter indício de caminho aberto e exigir porta/nó/cluster pertinentes |
| R11 | N-C | Mesmas lacunas de completude de R04; referências SG não interpretadas | **Revisar**: concluir restrição apenas com evidências suficientes |
| R12 | N-I; R01–R04 | HTTP/HTTPS fixos; correlação só primeiro hostname | **Revisar**: reaproveitar delegação, validar vínculo e portas |
| R13 | N-C; S12 para defaults de controlador, não toda semântica de Ingress | Default sem controlador/versionamento e inbound CIDRs apenas declarados | **Revisar**: indicar inferência de configuração e faltas; confirmar fonte de defaults ALB em etapa posterior |
| R14 | N-O/N-U | Manifesto não comprova caminho aplicado | **Revisar**: distinguir declaração de fallback e observação |
| R15 | N-U | Controlador fora do suporte não é evidência de abertura | **Manter como fallback**, com motivo “controlador não correlacionado” |
| R16 | N-I | Seleção do primeiro nginx, sem associação à classe nem namespace do controlador | **Revisar**: herança somente por vínculo demonstrado; caso contrário, inconclusiva |
| R17 | N-C; restrição em camada da rota é plausível | Herda high da nuvem para decisão reduzida só por manifesto; caminho direto pode contornar | **Revisar**: comprovar restrição no caminho afetado e recalcular suficiência |
| R18 | N-S; S2 não estabelece equivalência netpol→Small; S9 exige enforcement | Política de ingresso isolada não caracteriza rede altamente controlada; egress e transitividade ignorados | **Remover a implicação automática para Small** no modelo futuro; preservar netpol como evidência de restrição |
| R19 | N-C/N-U | Política permissiva não demonstra fronteira controlada; high injustificado | **Considerar inconclusiva** sem contexto adicional; Controlled apenas sob fronteira declarada/observada suficiente |
| R20 | N-C/N-U | Ausência de recurso não é prova negativa; rede pode ser amplamente acessível | **Considerar inconclusiva** sem inventário e fronteira; fallback operacional Open separado |

Resumo das recomendações: 15 revisar, 2 manter exclusivamente como fallback, 1 remover implicação automática, 2 considerar inconclusivas na ausência de evidências adicionais. Não são 20 falhas independentes: várias compartilham parsing, correlação e suficiência.

## 4. Pequena exposição: revisão específica

**Fato:** R18 é o único ramo que produz `small` (`analyze:267`); cenário 01 é o único rótulo small (`build_scenarios.py:61`). A regra não avalia interfaces desabilitadas, automação, comunicação dos outros hosts nem uso da função vulnerável. A política é resumida por `netpol_state:204–219`, que considera apenas parte dos seletores e regras.

**Interpretação:** o cenário 01 mostra restrição declarada de ingresso, mas não demonstra todas as premissas para Small. Não se deve trocar seu rótulo neste checkpoint nem alegar que o resultado atual foi cientificamente refutado por um único YAML; o que falta é evidência suficiente e justificativa independente.

**Proposta:** Small deve depender de um argumento explícito e rastreável de serviço local, rede altamente controlada ou código vulnerável inalcançável, compatível com a fonte normativa congelada. Se o protótipo não conseguir observar esses critérios no escopo mínimo, deve admitir cobertura pequena ou nula de Small sustentado, em vez de fabricar uma regra simples. A interface não precisa automatizar prova de inalcançabilidade de código; pode declarar essa capacidade fora do escopo.

## 5. Regras auxiliares que precisam acompanhar a revisão

| Mecanismo atual | Referência | Avaliação proposta |
|---|---|---|
| SG: união por sobreposição de portas; protocolos só distinguem `-1` | `exposure_analyzer.py:74–85` | Preservar extração, acrescentar semântica e diagnóstico de campos não suportados |
| NetworkPolicy: `matchLabels`; from vazio, namespaceSelector vazio ou CIDR universal → permissive | `200–219` | Revisar seleção, conjunção pod/namespace, portas, `except`, união e enforcement; uma aproximação não deve aparentar completude |
| hostNetwork/hostPort só geram notas | `257–258` | Capacidade não suportada deve impedir conclusão reduzida definitiva quando afetar o componente |
| TLS registrado, não altera nível | `166–167` | Manter ausência de redução automática por criptografia; não confundir TLS com restrição de origem |
| Política não reduz entrada externa | `263–265` | Manter cautela, mas uma restrição efetiva e pertinente pode ser analisada futuramente; evitar regra absoluta |
| Maior exposição; maior confiança no empate | `261–262` | Separar máximos de exposição e estado das evidências; não esconder faltas por desempate |
| Máximo global sem fronteira explícita | `274–275` | Manter como resumo opcional, não como substituto do componente afetado |

## 6. Cobertura e resultados

**Verificado neste CP01.1:** `.venv/bin/python run_scenarios.py`, com `PYTHONDONTWRITEBYTECODE=1`, reproduziu 16/16. O executor compara apenas `system_exposure` (`run_scenarios.py:10–18`), não valida cada regra, confiança, evidência ou correlação. Portanto, os cenários associados são cobertura de caminhos por inspeção e consistência de integração, não 20 testes unitários independentes.

Rótulos são definidos pelo autor no próprio gerador (`build_scenarios.py:2–3,60–84`); o README reconhece essa limitação (`README.md:29–30`). As fixtures atuais permanecem preservadas como regressão histórica, sem promoção a gabarito normativo independente.
