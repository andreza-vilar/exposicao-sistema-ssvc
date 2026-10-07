#!/usr/bin/env python3
"""
Componente de Exposição do Sistema (versão base) — SSVC.

Estima o valor do ponto de decisão "Exposição do Sistema" (small | controlled | open)
a partir de (1) manifestos Kubernetes e (2) um snapshot de fatos do provedor de nuvem
(saídas JSON da AWS CLI). Determinístico: nenhuma LLM decide o que é analisado.

Uso:
  python exposure_analyzer.py --manifests DIR [--cloud cloud.json] [--format json|text]
"""
import argparse
import json
import sys
from pathlib import Path

import yaml

LEVELS = ["small", "controlled", "open"]
RANK = {l: i for i, l in enumerate(LEVELS)}
CONF = {"low": 0, "medium": 1, "high": 2}
OPEN_CIDRS = {"0.0.0.0/0", "::/0"}
NODEPORT_RANGE = (30000, 32767)


# ----------------------------------------------------------------- carga
def load_manifests(path):
    p = Path(path)
    files = [p] if p.is_file() else sorted(list(p.rglob("*.yaml")) + list(p.rglob("*.yml")))
    objs = []
    for f in files:
        with open(f) as fh:
            for doc in yaml.safe_load_all(fh):
                if not doc:
                    continue
                if doc.get("kind") == "List":
                    objs.extend(doc.get("items", []))
                else:
                    objs.append(doc)
    return objs


def meta(o):
    m = o.get("metadata", {})
    return m.get("namespace", "default"), m.get("name", "?")


def ann(o):
    return o.get("metadata", {}).get("annotations", {}) or {}


def lb_hostname(o):
    ing = (o.get("status", {}) or {}).get("loadBalancer", {}).get("ingress", [])
    return ing[0].get("hostname") if ing else None


def split_cidrs(v):
    return [c.strip() for c in str(v).split(",") if c.strip()]


# ----------------------------------------------------------------- nuvem
class Cloud:
    """Fatos do provedor (formato AWS CLI: elbv2 describe-load-balancers,
    ec2 describe-security-groups; 'Nodes' é um resumo de describe-instances)."""

    def __init__(self, data):
        self.lbs = data.get("LoadBalancers", [])
        self.sgs = {s["GroupId"]: s for s in data.get("SecurityGroups", [])}
        self.nodes = data.get("Nodes", [])

    def lb_by_dns(self, host):
        return next((lb for lb in self.lbs if lb.get("DNSName") == host), None)

    def inbound_cidrs(self, sg_ids, ranges):
        """CIDRs de origem permitidos pelos SGs para algum dos intervalos de porta."""
        out = set()
        for sid in sg_ids:
            for perm in self.sgs.get(sid, {}).get("IpPermissions", []):
                lo, hi = perm.get("FromPort", 0), perm.get("ToPort", 65535)
                if perm.get("IpProtocol") == "-1":
                    lo, hi = 0, 65535
                if any(lo <= rh and rl <= hi for rl, rh in ranges):
                    out.update(r["CidrIp"] for r in perm.get("IpRanges", []))
                    out.update(r["CidrIpv6"] for r in perm.get("Ipv6Ranges", []))
        return out


def eval_lb(lb, cloud, ranges):
    """Nível de um balanceador a partir de fatos reais da nuvem."""
    ev = [f"[nuvem] LB {lb.get('LoadBalancerName', '?')}: Scheme={lb.get('Scheme')}"]
    if lb.get("Scheme") == "internal":
        return "controlled", ev + ["[nuvem] LB interno: sem endereço público"]
    sgs = lb.get("SecurityGroups", [])
    if not sgs:
        return "open", ev + ["[nuvem] LB voltado à internet sem security group: sem filtro de origem no LB"]
    cidrs = cloud.inbound_cidrs(sgs, ranges)
    ev.append(f"[nuvem] entrada permitida pelos SGs do LB: {sorted(cidrs) or 'nenhuma'}")
    if cidrs & OPEN_CIDRS:
        return "open", ev
    return "controlled", ev


# ------------------------------------------------------------ pontos de entrada
class Entry:
    def __init__(self, kind, name, level, conf, ev):
        self.kind, self.name, self.level, self.conf, self.ev = kind, name, level, conf, ev

    def as_dict(self):
        return {"entrypoint": f"{self.kind}/{self.name}", "level": self.level,
                "confidence": self.conf, "evidence": self.ev}


def service_entry(svc, cloud):
    ns, name = meta(svc)
    spec, a = svc.get("spec", {}), ann(svc)
    t = spec.get("type", "ClusterIP")
    ports = spec.get("ports", [])
    if t == "LoadBalancer":
        svc_ranges = [(p["port"], p["port"]) for p in ports if "port" in p] or [(0, 65535)]
        # Controlador novo da AWS cria LB interno por padrão; o legado, internet-facing.
        managed = (a.get("service.beta.kubernetes.io/aws-load-balancer-type") in ("external", "nlb-ip")
                   or spec.get("loadBalancerClass") == "service.k8s.aws/nlb")
        scheme = a.get("service.beta.kubernetes.io/aws-load-balancer-scheme")
        internal = (a.get("service.beta.kubernetes.io/aws-load-balancer-internal") == "true"
                    or scheme == "internal" or (managed and scheme != "internet-facing"))
        src = spec.get("loadBalancerSourceRanges")
        ev = [f"[manifesto] Service {ns}/{name} type=LoadBalancer"]
        host = lb_hostname(svc)
        lb = cloud.lb_by_dns(host) if (cloud and host) else None
        manifest_level = ("controlled" if internal else
                          "controlled" if src and not (set(src) & OPEN_CIDRS) else "open")
        if src:
            ev.append(f"[manifesto] loadBalancerSourceRanges={src}")
        if internal:
            ev.append("[manifesto] anotação/controlador indica LB interno")
        if lb:
            level, cev = eval_lb(lb, cloud, svc_ranges)
            if level == "open" and src and not (set(src) & OPEN_CIDRS):
                ev.append("[divergência] manifesto restringe origens, mas a nuvem permite internet")
            return Entry("Service", f"{ns}/{name}", level, "high", ev + cev)
        ev.append("[aviso] sem fatos da nuvem para este LB: nível inferido só do manifesto")
        return Entry("Service", f"{ns}/{name}", manifest_level, "medium", ev)
    if t == "NodePort":
        rngs = [(p["nodePort"], p["nodePort"]) if "nodePort" in p else NODEPORT_RANGE for p in ports] or [NODEPORT_RANGE]
        ev = [f"[manifesto] Service {ns}/{name} type=NodePort"]
        if not cloud or not cloud.nodes:
            return Entry("Service", f"{ns}/{name}", "open", "low",
                         ev + ["[aviso] sem fatos da nuvem sobre os nós: pior caso assumido"])
        public = [n for n in cloud.nodes if n.get("PublicIpAddress")]
        if not public:
            return Entry("Service", f"{ns}/{name}", "controlled", "high",
                         ev + ["[nuvem] nós sem IP público"])
        cidrs = cloud.inbound_cidrs({g for n in public for g in n.get("SecurityGroupIds", [])}, rngs)
        ev += [f"[nuvem] {len(public)} nó(s) com IP público",
               f"[nuvem] entrada permitida nas portas do NodePort: {sorted(cidrs) or 'nenhuma'}"]
        return Entry("Service", f"{ns}/{name}", "open" if cidrs & OPEN_CIDRS else "controlled", "high", ev)
    return None  # ClusterIP / ExternalName


def ingress_entry(ing, svcs, cloud):
    ns, name = meta(ing)
    spec, a = ing.get("spec", {}), ann(ing)
    cls = spec.get("ingressClassName") or a.get("kubernetes.io/ingress.class") or ""
    hosts = [r.get("host", "*") for r in spec.get("rules", [])]
    ev = [f"[manifesto] Ingress {ns}/{name} class={cls or '(padrão)'} hosts={hosts}"]
    ev.append("[manifesto] TLS configurado (registrado; não altera o nível na versão base)"
              if spec.get("tls") else "[manifesto] sem TLS")
    ranges = [(80, 80), (443, 443)]
    if cls == "alb" or any(k.startswith("alb.ingress.kubernetes.io/") for k in a):
        scheme = a.get("alb.ingress.kubernetes.io/scheme", "internal")  # padrão do controlador
        cidrs = split_cidrs(a.get("alb.ingress.kubernetes.io/inbound-cidrs", "0.0.0.0/0"))
        ev.append(f"[manifesto] ALB scheme={scheme} inbound-cidrs={cidrs}")
        host = lb_hostname(ing)
        lb = cloud.lb_by_dns(host) if (cloud and host) else None
        if lb:
            level, cev = eval_lb(lb, cloud, ranges)
            return Entry("Ingress", f"{ns}/{name}", level, "high", ev + cev)
        level = "controlled" if scheme == "internal" or not (set(cidrs) & OPEN_CIDRS) else "open"
        return Entry("Ingress", f"{ns}/{name}", level, "medium",
                     ev + ["[aviso] sem fatos da nuvem para este ALB: nível inferido só do manifesto"])
    # Ingress em controlador dentro do cluster (ex.: ingress-nginx): exposição = Service do controlador
    ctrl = next((s for s in svcs
                 if (s.get("metadata", {}).get("labels", {}) or {}).get("app.kubernetes.io/name") == "ingress-nginx"
                 and s.get("spec", {}).get("type") in ("LoadBalancer", "NodePort")), None)
    if not ctrl:
        return Entry("Ingress", f"{ns}/{name}", "open", "low",
                     ev + ["[aviso] controlador de ingress não localizado nos manifestos: pior caso assumido"])
    e = service_entry(ctrl, cloud)
    ev += [f"[manifesto] exposição herdada do Service do controlador {e.name}"] + e.ev
    allow = split_cidrs(a.get("nginx.ingress.kubernetes.io/allowlist-source-range",
                              a.get("nginx.ingress.kubernetes.io/whitelist-source-range", "")))
    level, conf = e.level, e.conf
    if allow and not (set(allow) & OPEN_CIDRS) and level == "open":
        level = "controlled"
        ev.append(f"[manifesto] allowlist de origens no Ingress={allow} (restrição de acesso)")
    return Entry("Ingress", f"{ns}/{name}", level, conf, ev)


# ----------------------------------------------------------------- netpol
def selects(selector, labels):
    return all(labels.get(k) == v for k, v in (selector or {}).get("matchLabels", {}).items())


def netpol_state(policies, ns, labels):
    """'restrictive' | 'permissive' | 'none' para tráfego de entrada nos pods."""
    sel = [p for p in policies
           if meta(p)[0] == ns and selects(p["spec"].get("podSelector"), labels)
           and ("Ingress" in p["spec"].get("policyTypes", ["Ingress"]) or "ingress" in p["spec"])]
    if not sel:
        return "none", []
    for p in sel:
        for rule in p["spec"].get("ingress", []) or []:
            frm = rule.get("from")
            if not frm:
                return "permissive", [meta(p)[1]]
            for f in frm:
                if f.get("namespaceSelector") == {} or f.get("ipBlock", {}).get("cidr") in OPEN_CIDRS:
                    return "permissive", [meta(p)[1]]
    return "restrictive", [meta(p)[1] for p in sel]


# ----------------------------------------------------------------- análise
def analyze(objs, cloud=None):
    by = lambda k: [o for o in objs if o.get("kind") == k]
    workloads = [o for o in objs if o.get("kind") in ("Deployment", "StatefulSet", "DaemonSet", "ReplicaSet", "Pod")]
    svcs, ingresses, policies = by("Service"), by("Ingress"), by("NetworkPolicy")

    def pod_labels(w):
        if w["kind"] == "Pod":
            return w.get("metadata", {}).get("labels", {}) or {}
        return w.get("spec", {}).get("template", {}).get("metadata", {}).get("labels", {}) or {}

    def pod_spec(w):
        return w.get("spec", {}) if w["kind"] == "Pod" else w.get("spec", {}).get("template", {}).get("spec", {})

    result = []
    for w in workloads:
        ns, name = meta(w)
        labels = pod_labels(w)
        mine = [s for s in svcs if meta(s)[0] == ns and s.get("spec", {}).get("selector")
                and all(labels.get(k) == v for k, v in s["spec"]["selector"].items())]
        entries, notes = [], []
        for s in mine:
            e = service_entry(s, cloud)
            if e:
                entries.append(e)
        for ing in ingresses:
            if meta(ing)[0] != ns:
                continue
            backends = {p.get("backend", {}).get("service", {}).get("name")
                        for r in ing.get("spec", {}).get("rules", [])
                        for p in (r.get("http", {}) or {}).get("paths", [])}
            backends.add((ing.get("spec", {}).get("defaultBackend", {}) or {}).get("service", {}).get("name"))
            if any(meta(s)[1] in backends for s in mine):
                entries.append(ingress_entry(ing, svcs, cloud))
        ps = pod_spec(w)
        if ps.get("hostNetwork") or any("hostPort" in p for c in ps.get("containers", []) for p in c.get("ports", [])):
            notes.append("hostNetwork/hostPort detectado: fora do escopo da versão base (não avaliado)")
        state, pols = netpol_state(policies, ns, labels)
        if entries:
            top = max(entries, key=lambda e: (RANK[e.level], CONF[e.conf]))
            level, conf = top.level, top.conf
            if state != "none":
                notes.append(f"NetworkPolicy {pols} presente ({state}); efeito depende do CNI e do modo do LB — "
                             "não usada para reduzir o nível na versão base")
        else:
            level = "small" if state == "restrictive" else "controlled"
            conf = "high" if state != "none" else "medium"
            entries.append(Entry("Cluster", f"{ns}/{name}", level, conf,
                [f"[manifesto] sem Service externo (LoadBalancer/NodePort) nem Ingress",
                 f"[manifesto] NetworkPolicy de entrada: {state} {pols or ''}".strip()]))
        result.append({"workload": f"{kind_short(w)}/{ns}/{name}", "exposure": level, "confidence": conf,
                       "entrypoints": [e.as_dict() for e in entries], "notes": notes})
    system = max((r["exposure"] for r in result), key=RANK.get, default=None)
    return {"system_exposure": system, "workloads": result}


def kind_short(w):
    return w["kind"]


def render_text(res):
    out = [f"EXPOSIÇÃO DO SISTEMA (pior caso entre cargas de trabalho): {str(res['system_exposure']).upper()}"]
    for w in res["workloads"]:
        out.append(f"\n- {w['workload']}: {w['exposure']} (confiança {w['confidence']})")
        for e in w["entrypoints"]:
            out.append(f"    * {e['entrypoint']} -> {e['level']} ({e['confidence']})")
            out += [f"        {x}" for x in e["evidence"]]
        out += [f"    ! {n}" for n in w["notes"]]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifests", required=True)
    ap.add_argument("--cloud")
    ap.add_argument("--format", choices=["json", "text"], default="text")
    a = ap.parse_args()
    cloud = Cloud(json.load(open(a.cloud))) if a.cloud else None
    res = analyze(load_manifests(a.manifests), cloud)
    print(json.dumps(res, indent=2, ensure_ascii=False) if a.format == "json" else render_text(res))


if __name__ == "__main__":
    sys.exit(main())
