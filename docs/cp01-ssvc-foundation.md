# CP01.1 — Fundamentação científica de System Exposure

Data de consulta e execução: 26/11/2026 (America/Fortaleza). Estado: análise concluída; propostas ainda sujeitas à discussão com Andrey. Nenhuma mudança de implementação autorizada por este documento.

## 1. Método, fontes e limites

**Fatos verificados:** leitura integral via PDFKit das 16 páginas de `SSVC_Copilot.pdf` e dos 25 slides de `SSVC_Copilot_SBSeg2026.pdf`. A numeração abaixo é a posição da página no PDF, começando em 1. Diagramas e tabelas relevantes foram também renderizados e inspecionados, incluindo arquitetura, seção 5.2 e matrizes de avaliação. Os PDFs foram apenas lidos, sem edição ou inclusão no índice Git.

Identidade dos documentos locais (SHA-256):

| Documento | Hash |
|---|---|
| Artigo | `a6b012c2efd465b6cbb08a744be21987bbd8dc63fb6a22ad1a339c5dc7fffba8` |
| Apresentação | `4ef84e0c01726559c2897dd237f8c521e0ba755e6ba545df8888030001905726` |

As fontes oficiais públicas foram consultadas após a leitura integral. Não houve consultas a contas, APIs AWS, credenciais, profiles ou contextos Kubernetes. A página CISA citada no artigo e seu guia PDF retornaram HTTP 403; não se afirma leitura integral desses recursos. A fundamentação de exposição usa CERT/CC, referência também indicada no artigo, e distingue documentação viva de versão histórica efetivamente utilizada pelos autores.

Rótulos epistemológicos deste conjunto documental: **fato** = conteúdo lido ou execução observada; **interpretação** = conclusão analítica; **hipótese** = proposição a investigar; **proposta** = decisão futura sem implementação. Os arquivos complementares são [regras](cp01-rule-traceability.md), [decisões](cp01-design-decisions.md), [método experimental](cp01-experimental-methodology.md) e [próximos checkpoints](cp01-next-checkpoints.md).

## 2. Trabalho original: o que os autores afirmam

| Tema | Conteúdo documentado | Localização no artigo | Localização nos slides |
|---|---|---|---|
| Problema | Volume de vulnerabilidades e recursos limitados exigem priorização contextual; limiares de CVSS/EPSS não resolvem todo o problema | pp. 1–3, resumo e §1 | 2–4 |
| Objetivo | Assistente SSVC com enriquecimento por agentes e apoio humano–IA | pp. 2–3, §1 | 6–8 |
| Modelo | Modelo do implantador/deployer | p. 4, §2.4 | 5, 25 |
| Pontos | Exploração, exposição, automação e impacto humano | p. 4, §2.4 | 5, 25 |
| Arquitetura | Varredura de artefatos → CVEs → três agentes técnicos → fila → agente de impacto humano/operador → STIX | pp. 6–7, §5, Figura 1 | 7–8 |
| Exploração | KEV, exploits e referências, com EPSS/CWE complementares | pp. 7–8, §5.1 | 9, 11, 21 |
| Exposição | CVSS Attack Vector como evidência auxiliar, pior caso e revisão contextual | p. 8, §5.2 | 9 |
| Automação | Combinação AV:N, UI:N, AC:L, PR:N e evidência complementar de scripts/exploits | pp. 8–9, §5.3 | 9 |
| Fila | Usa decisões finais ainda alcançáveis sob diferentes impactos humanos | p. 9, §5.4 | 12 |
| Impacto humano | Calibração de pior caso e agente adaptativo com contexto acumulado; operador controla a decisão | pp. 9–10, §5.5, Figura 2 | 13–15 |
| Modelo de ameaça | CVEs conhecidos; admite falsos positivos de aplicabilidade; pressupõe integridade das ferramentas/agentes | p. 6, §4 | Sem detalhamento equivalente |

O emprego de agentes no Copilot não é requisito para a extensão determinística do TCC. A arquitetura publicada não demonstra, por si só, uso de LLM em todos os pontos técnicos. O artigo não substitui a inspeção de sua implementação original.

### 2.1. Seção 5.2: limites do que pode ser reconstruído

**Afirmação dos autores:** exposição depende principalmente da configuração do serviço; determinar a exposição real exige contexto de rede, arquitetura e operação. Attack Vector auxilia a inferência inicial conservadora. Vulnerabilidades remotas tendem a aumentar a exposição inferida; as locais recebem valores mais moderados mesmo em serviços na Internet. O operador pode ajustar o valor e reutilizá-lo no mesmo serviço (artigo, p. 8, §5.2; slide 9).

**Ausência documental verificada:** a seção não apresenta tabela exata AV→Small/Controlled/Open, tratamento de CVSS ausente ou conflitante, prioridade entre versões CVSS, algoritmo de persistência nem testes específicos do agente de exposição. Não é possível reconstruir B0 fielmente apenas desse texto.

**Interpretação do TCC:** há uma oportunidade de testar a utilidade de evidências operacionais para a inferência inicial, preservando a distinção entre contexto de implantação e propriedades da vulnerabilidade. Não se conclui que todo AV:N esteja aberto, nem que AV:L determine Small, nem que o Copilot ignore o contexto fornecido por seu operador.

### 2.2. Avaliação apresentada e alcance dos resultados

| Avaliação dos autores | Procedimento/resultado reportado | Localização |
|---|---|---|
| Exploração | Comparação com CISA Vulnrichment; 65,31% na configuração final; 97,18% sem regras EPSS/CWE e com exclusão de evidências indisponíveis | artigo pp. 10–11, §§6/6.1, Tabela 2; slides 11/21 |
| Automação | 92,80%; texto informa 133.442 concordâncias e 10.721 divergências | artigo p. 11, §6.2, Tabela 3; slide 10 |
| Impacto humano | Cinco participantes e 16 CVEs de bombas de insulina; comparação entre sugestão, pior caso e decisão do operador | artigo pp. 12–14, §6.3; slides 16–18/23–24 |
| Resultados de impacto | 78,75% de concordância da IA; 52,5% do pior caso; erro médio reportado ≈0,28 e 0,55 | artigo p. 13, §6.3.2; slide 17 |
| System Exposure | Não há subseção, matriz ou métrica específica de avaliação desse ponto | inspeção integral do §6, pp. 10–14; slides de resultados 10–11/16–18/21–24 |

**Interpretação:** as concordâncias dos outros agentes não são evidência de acurácia de System Exposure. A existência de estudo humano no Copilot não obriga este TCC a adotar participantes humanos. A ausência de avaliação específica na publicação não prova que nunca tenham existido testes internos.

**Inconsistência verificável na cópia fornecida:** as células da Tabela 2a e da Tabela 3 somam 143.796; o texto usa 144.163. Na Tabela 3, as divergências somam 8.191 + 2.163 = 10.354, enquanto o texto usa 10.721. A diagonal soma 133.442 e, dividida por 143.796, resulta em 92,7995%, compatível com 92,80%. Esses números também aparecem nos slides 10–11. Causa desconhecida: solicitar a Jan denominadores, filtros e versão dos dados. Não corrigir os resultados publicados nem usar esses totais como tamanho da avaliação do TCC.

## 3. Modelo e versões do SSVC

**Identificação segura:** modelo tradicional do **deployer** com quatro pontos e saídas Defer, Scheduled, Out-of-Cycle e Immediate (artigo p. 4, §2.4; slide 25). **A versão exata do framework e o commit da árvore utilizados pelo Copilot não são informados nos PDFs.** Datas das referências não demonstram pin de versão.

| Artefato | O que foi verificado | Uso neste TCC |
|---|---|---|
| SSVC 2.0, SEI, 30/04/2021 | Relatório histórico de um framework modular com diferentes stakeholders [S4] | Contexto histórico; não afirmar que é a versão executada pelo Copilot |
| SSVC v2.1 / v2023.7 | Release oficial registra esclarecimento sobre código vulnerável inalcançável e Small [S5] | Referência histórica de mudança |
| Documentação CERT/CC consultada | Deployer conserva os quatro pontos; referência de exposição identifica `ssvc:EXP:1.0.1` [S1–S3] | Base semântica proposta, com data de consulta |
| Versão anterior do ponto | A página identifica `EXP:1.0.0` com Unavoidable/U no terceiro valor; a atual usa Open/O [S1] | Não misturar códigos sem conversão explícita |
| Evolução de publicação | SEI descreve release 2025.9 e evolução de schemas [S6] | Versão de publicação não é versão do ponto nem prova da versão do Copilot |
| CISA Coordinator | Modelo distinto, com Technical Impact e Mission & Well-being, saídas Track/Track*/Attend/Act [S7] | Não substituir o deployer por esse modelo |

**Proposta:** fixar a semântica `ssvc:EXP:1.0.1` e uma revisão imutável da fonte antes da implementação experimental. Até confirmar com Jan, descrever isso como compatibilidade semântica com os valores publicados, não identidade histórica comprovada. A documentação viva foi consultada em 26/11/2026; não se atribui a ela um release exato sem verificação.

## 4. Definições oficiais e aplicação

Paráfrase de [S1], seção “System Exposure”, versão do ponto `1.0.1`: exposição é a superfície acessível do sistema ou serviço afetado.

| Valor oficial | Síntese |
|---|---|
| Small | Programa/serviço local ou rede altamente controlada |
| Controlled | Serviço em rede com restrições ou mitigações efetivas; pode abranger encadeamento de vulnerabilidades |
| Open | Internet ou outra rede amplamente acessível cujo acesso não possa ser controlado de forma plausível |

A mesma referência orienta usar Open quando a exposição é desconhecida e avaliar o contexto real de implantação; reconhece que a fronteira Small/Controlled não é perfeitamente precisa [S1].

O guia [S2], seção “Small versus Controlled”, apresenta heurísticas **ordenadas**, após excluir Open: interfaces desabilitadas/removidas; Automatable=yes; presença de hosts com web/email na rede; funcionalidade vulnerável de biblioteca não utilizada e inalcançável. São orientações contextuais, não uma regra oficial “NetworkPolicy → Small”. O guia também diferencia uma instância concreta de uma generalização sobre todos os sistemas de um tipo.

### 4.1. Relação com CVSS e com o componente afetado

Na especificação CVSS 3.1, §2.1.1, Attack Vector descreve o contexto de exploração do componente; Network também pode ser usado em uma intranet. Mitigações específicas do alvo pertencem ao grupo Environmental, conforme §2.1 [S8]. **Interpretação:** AV é informação auxiliar de natureza diferente da exposição operacional; não comprova o caminho Internet→componente.

O texto SEI de 2026 destaca exposição e impacto humano como atributos do sistema reutilizáveis entre vulnerabilidades [S6, “Today, Deployers Can Readily Adopt SSVC”]. O guia detalhado admite variação entre componentes [S2]. **Interpretação conciliadora:** reutilizar exposição quando componente, configuração e caminhos relevantes forem os mesmos; não transferir automaticamente o nível de um frontend a toda biblioteca ou banco de dados da aplicação.

### 4.2. Ambiguidades Kubernetes/AWS a resolver

As conclusões seguintes são **interpretações de engenharia**, não novas definições oficiais SSVC:

- ClusterIP é um mecanismo de serviço; sua ausência de publicação direta não comprova rede altamente controlada. A aplicação pode possuir outro caminho de entrada.
- NetworkPolicy é declaração cuja aplicação depende do plugin de rede; políticas são aditivas, não uma lista de bloqueios com precedência [S9, “Prerequisites”/“The two sorts of Pod isolation”].
- Um SG aberto informa permissão na borda, mas não demonstra sozinho listener, encaminhamento ao alvo e interface do componente afetado; SGs de ALB controlam portas/protocolos e também a comunicação com targets [S11].
- “internal” limita uma modalidade de publicação; não caracteriza todos os consumidores e caminhos alternativos.
- Defaults AWS dependem de controlador e versão: a documentação de annotations distingue o controlador AWS do legado e do Auto Mode [S12].
- Ausência de recurso num conjunto de YAMLs é diferente de inventário completo demonstrando sua inexistência.
- Observação de conectividade não equivale a prova de exploração; ambos devem permanecer separados.

## 5. Delimitação da contribuição científica proposta

**Problema de pesquisa:** a inferência de exposição sem descrição explícita da implantação pode não distinguir ambientes do mesmo componente com acessibilidade diferente; o protótipo atual incorpora contexto, mas carece de critérios rastreáveis e tratamento de evidência insuficiente.

**Questão principal:** em cenários controlados Kubernetes/AWS, como a incorporação de evidências operacionais altera a concordância normativa, a direção das divergências e a suficiência das classificações de System Exposure, comparada à abordagem original confirmada do Copilot?

**Hipótese H1:** mantendo componente, manifestos e condições de avaliação constantes, snapshots AWS completos e correlacionados podem resolver ambiguidades de B1 e reduzir classificações conservadoras sem aumentar subestimativas nos cenários avaliados. A hipótese pode não se confirmar; não se presume ganho universal. B0 permite comparação adicional quando disponível, sem substituir a ablação B1/B2.

**Objetivo geral:** propor e avaliar um classificador determinístico de System Exposure baseado em evidências Kubernetes/AWS, com justificativas rastreáveis e limites explícitos.

**Objetivos específicos:** (1) formalizar interpretação normativa; (2) associar componente e implantação; (3) distinguir evidência e fallback; (4) preservar e ampliar testes em etapa futura; (5) comparar B1/B2 e B0 confirmado; (6) analisar divergências e ameaças à validade.

**Contribuições esperadas:** modelo operacional documentado; representação auditável de evidências; protocolo reproduzível e corpus controlado; resultados sobre contribuição incremental de nuvem. Não se reivindica novo SSVC, superioridade já demonstrada ou validação independente pelos atuais 16 rótulos.

**Relação com Copilot:** complemento independente para o ponto exposição, com possível adaptador futuro. Não reproduz agentes, fila, impacto humano ou integração completa STIX. Escopo mínimo proposto: SSVC tradicional, Kubernetes, AWS, determinismo, evidências e avaliação. Excluídos: AI-SSVC, LLMs decisores, outros provedores, GUI, mesh, Gateway API abrangente e estudo humano. Tudo sujeito ao alinhamento científico.

## 6. Referências e registro de consulta

Todos os links abaixo foram consultados em **26/11/2026**. As páginas vivas não demonstram a revisão histórica usada pelos autores. Links falhos não foram usados como conteúdo lido.

| ID | Referência / versão / seção | URL e condição |
|---|---|---|
| P1 | Filho, Albuquerque, Falcão e Brito. SSVC Copilot; 16 páginas; §§2.4, 4–7, especialmente §5.2 | [PDF local](../SSVC_Copilot.pdf); leitura integral |
| P2 | Mesmos autores. Apresentação SBSeg 2026; 25 slides | [PDF local](../SSVC_Copilot_SBSeg2026.pdf); leitura integral |
| S1 | CERT/CC. System Exposure; `ssvc:EXP:1.0.1`; definições, default, prior versions | https://certcc.github.io/SSVC/reference/decision_points/system_exposure/ |
| S2 | CERT/CC. Gathering Information About System Exposure; contexto e Small versus Controlled | https://certcc.github.io/SSVC/howto/gathering_info/system_exposure/ |
| S3 | CERT/CC. Deployer Decision Model; Units of Work, Decision Points, Outcomes | https://certcc.github.io/SSVC/howto/deployer_tree/ ; link indicado na p. 4 do artigo |
| S4 | SEI. Prioritizing Vulnerability Response: SSVC Version 2.0; 30/04/2021; abstract | https://www.sei.cmu.edu/library/prioritizing-vulnerability-response-a-stakeholder-specific-vulnerability-categorization-version-20/ ; página bibliográfica consultada, não alegada leitura integral do relatório |
| S5 | CERT/CC. Release SSVC v2.1 (v2023.7); esclarecimento unreachable code | https://github.com/CERTCC/SSVC/releases/tag/v2.1 |
| S6 | Metcalf, Householder e Sarvepalli. From Concept to Practice; 28/01/2026; Today, Deployers… / Improving Vulnerability Data Format Records | https://www.sei.cmu.edu/blog/from-concept-to-practice-how-ssvc-has-evolved-to-make-adoption-possible/ |
| S7 | CERT/CC. CISA Coordinator v2.0.3; árvore JSON | https://github.com/CERTCC/SSVC/blob/main/docs/ssvc-calc/CISA-Coordinator.json ; conteúdo consultado no resultado da busca pública |
| S8 | FIRST. CVSS v3.1 Specification; §§2.1/2.1.1 | https://www.first.org/cvss/v3.1/specification-document |
| S9 | Kubernetes. Network Policies; documentação viva, página consultada identifica v1.37; prerequisites/isolation | https://kubernetes.io/docs/concepts/services-networking/network-policies/ ; não representa versão do cluster experimental |
| S10 | Kubernetes. Service; tipos de serviço; documentação viva | https://kubernetes.io/docs/concepts/services-networking/service/ |
| S11 | AWS. Security groups for your Application Load Balancer; considerações e regras | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-update-security-groups.html ; apenas documentação pública |
| S12 | AWS Load Balancer Controller. Service annotations; latest; defaults e distinção de controladores | https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/service/annotations/ ; versão experimental ainda não fixada |
| S13 | CERT/CC. SSVC and Asset Management; inventário e associação | https://certcc.github.io/SSVC/topics/asset_management/ |
| S14 | CERT/CC. Release notes / mudança da documentação para releases | https://github.com/CERTCC/SSVC/releases ; https://certcc.github.io/SSVC/about/changelog/ |
| B1 | CISA. SSVC; referência do artigo | https://www.cisa.gov/ssvc ; HTTP 403, conteúdo não lido |
| B2 | CISA. SSVC Guide | https://www.cisa.gov/sites/default/files/publications/cisa-ssvc-guide%20508c.pdf ; HTTP 403, conteúdo não lido |

## 7. Evidência operacional complementar

Execução local sem instalação, sem regenerar cenários:

```sh
.venv/bin/python -c 'import sys,yaml; print(sys.version); print(yaml.__version__)'
/usr/bin/time -p env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python run_scenarios.py
```

**Observado:** Python 3.9.6, PyYAML 6.0.3; 16/16 concordâncias; small=1, controlled=9, open=6; zero subestimativas/superestimativas. Tempo real 0,06 s, user 0,04 s, sys 0,00 s, código de saída 0. Os rótulos pertencem ao gerador atual (`build_scenarios.py:60–84`); a comparação é de `system_exposure` (`run_scenarios.py:10–24`). É teste de consistência interna, não validação científica independente.
