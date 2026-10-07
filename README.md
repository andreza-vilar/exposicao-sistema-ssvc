# Componente de Exposição do Sistema — versão base (protótipo do Marco 2)

Estima o ponto de decisão "Exposição do Sistema" do SSVC (small | controlled | open)
a partir de manifestos Kubernetes e de um snapshot de fatos do provedor de nuvem (AWS).
Determinístico e auditável: cada decisão vem com a lista de evidências e um nível de confiança.

## Uso
    pip install pyyaml
    python exposure_analyzer.py --manifests DIR_OU_ARQUIVO [--cloud cloud.json] [--format json|text]
    python build_scenarios.py && python run_scenarios.py     # suíte sintética

## Entrada de nuvem (cloud.json)
Chaves `LoadBalancers` (elbv2 describe-load-balancers), `SecurityGroups` (ec2 describe-security-groups)
e `Nodes` (resumo de describe-instances: PublicIpAddress, SecurityGroupIds).
Para ligar um Service/Ingress ao LB, os manifestos devem trazer `status.loadBalancer.ingress[].hostname`
(ex.: `kubectl get svc,ing -A -o yaml`).

## Regras (hipótese de trabalho, a validar com orientador)
- Alcançável da internet (LB/ALB internet-facing com origem 0.0.0.0/0; NodePort em nó público com SG aberto) -> open
- Alcançável só de origens restritas ou de rede privada (LB interno, allowlist, nós privados) -> controlled
- Sem entrada externa + NetworkPolicy de entrada restritiva -> small; sem NetworkPolicy ou permissiva -> controlled
- Fatos da nuvem prevalecem sobre o manifesto (divergência registrada). Sem fatos da nuvem: nível inferido do manifesto, confiança reduzida; caso desconhecido -> pior caso.
- Nível do sistema = o maior nível entre as cargas de trabalho.
- TLS e NetworkPolicy em caminho externo são registrados como evidência, mas NÃO alteram o nível na versão base.

## Limitações conhecidas
Apenas AWS (formato AWS CLI); sem coleta ao vivo (snapshot offline); hostNetwork/hostPort apenas sinalizados;
Gateway API, service mesh, WAF e autenticação na borda não avaliados; AWS LB Controller assumido com padrões
documentados (scheme interno por padrão) não verificado contra conta real. Os 16 cenários sintéticos têm rótulo
definido pelo autor: verificam a implementação, não a validade das regras.
