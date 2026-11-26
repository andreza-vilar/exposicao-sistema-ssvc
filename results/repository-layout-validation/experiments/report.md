# CP01.2 — Comparação preliminar B1 × B2

Concordância com rótulos sintéticos históricos; não é acurácia científica.

Confiança heurística legada (low/medium/high), não calibrada.

B0 pendente de confirmação com Jan; não executado. Classificador histórico preservado.

## Protocolo e arquitetura

Descoberta local → leitura/hash/validação → parser histórico → cópias dos mesmos objetos para B1/B2 → análise histórica → pareamento → métricas → exportação.

B1 mantém annotations AWS do manifesto. B2 acrescenta somente JSON sintético. Nenhum YAML foi aplicado e nenhum snapshot foi obtido de serviço real.

Hashes e versões: `summary.json`; outputs completos e evidências: `raw_results.json`; diferenças textuais de evidência: `paired_comparison.csv`.

## Execuções individuais

| Cenário | Histórico | B1 / confiança por workload | B2 / confiança por workload | Status B2 |
|---|---|---|---|---|
| 01-clusterip-netpol-restritiva | small | small / {"Deployment/demo/app": "high"} | None / {} | not_applicable |
| 02-clusterip-sem-netpol | controlled | controlled / {"Deployment/demo/app": "medium"} | None / {} | not_applicable |
| 03-clusterip-netpol-permissiva | controlled | controlled / {"Deployment/demo/app": "high"} | None / {} | not_applicable |
| 04-lb-aberto-confirmado-nuvem | open | open / {"Deployment/demo/app": "medium"} | open / {"Deployment/demo/app": "high"} | ok |
| 05-lb-interno-confirmado-nuvem | controlled | controlled / {"Deployment/demo/app": "medium"} | controlled / {"Deployment/demo/app": "high"} | ok |
| 06-lb-allowlist-confirmada | controlled | controlled / {"Deployment/demo/app": "medium"} | controlled / {"Deployment/demo/app": "high"} | ok |
| 07-lb-allowlist-no-manifesto-mas-nuvem-aberta | open | controlled / {"Deployment/demo/app": "medium"} | open / {"Deployment/demo/app": "high"} | ok |
| 08-lb-sem-fatos-de-nuvem | open | open / {"Deployment/demo/app": "medium"} | None / {} | not_applicable |
| 09-alb-internet-facing | open | open / {"Deployment/demo/app": "medium"} | open / {"Deployment/demo/app": "high"} | ok |
| 10-alb-interno-padrao | controlled | controlled / {"Deployment/demo/app": "medium"} | None / {} | not_applicable |
| 11-nginx-lb-aberto | open | open / {"Deployment/demo/app": "medium"} | open / {"Deployment/demo/app": "high"} | ok |
| 12-nginx-lb-aberto-com-allowlist | controlled | controlled / {"Deployment/demo/app": "medium"} | controlled / {"Deployment/demo/app": "high"} | ok |
| 13-nodeport-nos-privados | controlled | open / {"Deployment/demo/app": "low"} | controlled / {"Deployment/demo/app": "high"} | ok |
| 14-nodeport-nos-publicos-sg-aberto | open | open / {"Deployment/demo/app": "low"} | open / {"Deployment/demo/app": "high"} | ok |
| 15-nodeport-nos-publicos-sg-restrito | controlled | open / {"Deployment/demo/app": "low"} | controlled / {"Deployment/demo/app": "high"} | ok |
| 16-nlb-controlador-aws-padrao-interno | controlled | controlled / {"Deployment/demo/app": "medium"} | None / {} | not_applicable |

## Pares elegíveis

| Cenário | B1 → B2 | Grupo | Concordância histórica |
|---|---|---|---|
| 04-lb-aberto-confirmado-nuvem | open → open | confidence_only | unchanged |
| 05-lb-interno-confirmado-nuvem | controlled → controlled | confidence_only | unchanged |
| 06-lb-allowlist-confirmada | controlled → controlled | confidence_only | unchanged |
| 07-lb-allowlist-no-manifesto-mas-nuvem-aberta | controlled → open | increase | gained |
| 09-alb-internet-facing | open → open | confidence_only | unchanged |
| 11-nginx-lb-aberto | open → open | confidence_only | unchanged |
| 12-nginx-lb-aberto-com-allowlist | controlled → controlled | confidence_only | unchanged |
| 13-nodeport-nos-privados | open → controlled | decrease | gained |
| 14-nodeport-nos-publicos-sg-aberto | open → open | confidence_only | unchanged |
| 15-nodeport-nos-publicos-sg-restrito | open → controlled | decrease | gained |

## Métricas e denominadores

| Conjunto | Configuração | Execuções OK | Small / Controlled / Open | Concordância histórica | Subestimativas | Superestimativas |
|---|---|---|---|---|---|---|
| all_scenarios | B1 | 16 | 1 / 8 / 7 | 13/16 (81.2%) | 1/16 (6.2%) | 2/16 (12.5%) |
| all_scenarios | B2 | 10 | 0 / 5 / 5 | 10/10 (100.0%) | 0/10 (0.0%) | 0/10 (0.0%) |
| paired_subset | B1 | 10 | 0 / 4 / 6 | 7/10 (70.0%) | 1/10 (10.0%) | 2/10 (20.0%) |
| paired_subset | B2 | 10 | 0 / 5 / 5 | 10/10 (100.0%) | 0/10 (0.0%) | 0/10 (0.0%) |

Matriz B1 → B2 (linhas B1; colunas B2):

| B1 / B2 | small | controlled | open |
|---|---|---|---|
| small | 0 | 0 | 0 |
| controlled | 0 | 3 | 1 |
| open | 0 | 2 | 4 |

Mudanças de categoria: 3/10 (30.0%).
Grupos mutuamente exclusivos: `{"increase": 1, "decrease": 2, "confidence_only": 7, "unchanged": 0}`.

## Não aplicáveis e erros

- 01-clusterip-netpol-restritiva / B2: not_applicable; motivo=snapshot_missing; erros=[]
- 02-clusterip-sem-netpol / B2: not_applicable; motivo=snapshot_missing; erros=[]
- 03-clusterip-netpol-permissiva / B2: not_applicable; motivo=snapshot_missing; erros=[]
- 08-lb-sem-fatos-de-nuvem / B2: not_applicable; motivo=snapshot_missing; erros=[]
- 10-alb-interno-padrao / B2: not_applicable; motivo=snapshot_missing; erros=[]
- 16-nlb-controlador-aws-padrao-interno / B2: not_applicable; motivo=snapshot_missing; erros=[]
Nenhum erro de entrada ou classificação registrado.

## Diferenças de evidências e interpretação

### 04-lb-aberto-confirmado-nuvem
Categoria: open → open; confiança legada: {'Deployment/demo/app': 'medium'} → {'Deployment/demo/app': 'high'}.
- Evidência adicionada: [nuvem] LB a: Scheme=internet-facing
- Evidência adicionada: [nuvem] entrada permitida pelos SGs do LB: ['0.0.0.0/0']
- Evidência substituída/retirada: [aviso] sem fatos da nuvem para este LB: nível inferido só do manifesto

### 05-lb-interno-confirmado-nuvem
Categoria: controlled → controlled; confiança legada: {'Deployment/demo/app': 'medium'} → {'Deployment/demo/app': 'high'}.
- Evidência adicionada: [nuvem] LB b: Scheme=internal
- Evidência adicionada: [nuvem] LB interno: sem endereço público
- Evidência substituída/retirada: [aviso] sem fatos da nuvem para este LB: nível inferido só do manifesto

### 06-lb-allowlist-confirmada
Categoria: controlled → controlled; confiança legada: {'Deployment/demo/app': 'medium'} → {'Deployment/demo/app': 'high'}.
- Evidência adicionada: [nuvem] LB c: Scheme=internet-facing
- Evidência adicionada: [nuvem] entrada permitida pelos SGs do LB: ['198.51.100.0/24']
- Evidência substituída/retirada: [aviso] sem fatos da nuvem para este LB: nível inferido só do manifesto

### 07-lb-allowlist-no-manifesto-mas-nuvem-aberta
Categoria: controlled → open; confiança legada: {'Deployment/demo/app': 'medium'} → {'Deployment/demo/app': 'high'}.
- Evidência adicionada: [divergência] manifesto restringe origens, mas a nuvem permite internet
- Evidência adicionada: [nuvem] LB d: Scheme=internet-facing
- Evidência adicionada: [nuvem] entrada permitida pelos SGs do LB: ['0.0.0.0/0']
- Evidência substituída/retirada: [aviso] sem fatos da nuvem para este LB: nível inferido só do manifesto

### 09-alb-internet-facing
Categoria: open → open; confiança legada: {'Deployment/demo/app': 'medium'} → {'Deployment/demo/app': 'high'}.
- Evidência adicionada: [nuvem] LB e: Scheme=internet-facing
- Evidência adicionada: [nuvem] entrada permitida pelos SGs do LB: ['0.0.0.0/0']
- Evidência substituída/retirada: [aviso] sem fatos da nuvem para este ALB: nível inferido só do manifesto

### 11-nginx-lb-aberto
Categoria: open → open; confiança legada: {'Deployment/demo/app': 'medium'} → {'Deployment/demo/app': 'high'}.
- Evidência adicionada: [nuvem] LB ngx: Scheme=internet-facing
- Evidência adicionada: [nuvem] entrada permitida pelos SGs do LB: ['0.0.0.0/0']
- Evidência substituída/retirada: [aviso] sem fatos da nuvem para este LB: nível inferido só do manifesto

### 12-nginx-lb-aberto-com-allowlist
Categoria: controlled → controlled; confiança legada: {'Deployment/demo/app': 'medium'} → {'Deployment/demo/app': 'high'}.
- Evidência adicionada: [nuvem] LB ngx: Scheme=internet-facing
- Evidência adicionada: [nuvem] entrada permitida pelos SGs do LB: ['0.0.0.0/0']
- Evidência substituída/retirada: [aviso] sem fatos da nuvem para este LB: nível inferido só do manifesto

### 13-nodeport-nos-privados
Categoria: open → controlled; confiança legada: {'Deployment/demo/app': 'low'} → {'Deployment/demo/app': 'high'}.
- Evidência adicionada: [nuvem] nós sem IP público
- Evidência substituída/retirada: [aviso] sem fatos da nuvem sobre os nós: pior caso assumido

### 14-nodeport-nos-publicos-sg-aberto
Categoria: open → open; confiança legada: {'Deployment/demo/app': 'low'} → {'Deployment/demo/app': 'high'}.
- Evidência adicionada: [nuvem] 1 nó(s) com IP público
- Evidência adicionada: [nuvem] entrada permitida nas portas do NodePort: ['0.0.0.0/0']
- Evidência substituída/retirada: [aviso] sem fatos da nuvem sobre os nós: pior caso assumido

### 15-nodeport-nos-publicos-sg-restrito
Categoria: open → controlled; confiança legada: {'Deployment/demo/app': 'low'} → {'Deployment/demo/app': 'high'}.
- Evidência adicionada: [nuvem] 1 nó(s) com IP público
- Evidência adicionada: [nuvem] entrada permitida nas portas do NodePort: ['198.51.100.0/24']
- Evidência substituída/retirada: [aviso] sem fatos da nuvem sobre os nós: pior caso assumido

## Limitações

- Corpus pequeno, sintético e com rótulos definidos pelo autor; B2 não é gabarito de B1.
- Comparação pareada usa somente execuções OK de ambos os modos; não aplicáveis e erros permanecem exportados.
- Unidade e máximo global são os do classificador legado; nenhuma revisão científica das regras foi implementada.
- Confiança high não é evidência de acerto ou probabilidade calibrada; a diferença de strings não prova causalidade.
- O executor não cria indicadores novos de suficiência/fallback. Validação JSON é estrutural, não verificação de infraestrutura.
- Tempos e timestamp variam; classificações e métricas categóricas são determinísticas para as mesmas entradas.

Tempo total antes da exportação: 0.030618 s.
