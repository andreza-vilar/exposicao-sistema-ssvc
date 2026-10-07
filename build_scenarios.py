#!/usr/bin/env python3
"""Gera a suíte sintética de cenários (manifestos + snapshot de nuvem + rótulo esperado).
Rótulos definidos pela construção do cenário (autoria do desenvolvedor)."""
import json, os, shutil
from pathlib import Path

ROOT = Path(__file__).parent / "scenarios"
if ROOT.exists():
    shutil.rmtree(ROOT)

DEPLOY = """apiVersion: apps/v1
kind: Deployment
metadata: {name: app, namespace: demo}
spec:
  selector: {matchLabels: {app: web}}
  template:
    metadata: {labels: {app: web}}
    spec: {containers: [{name: web, image: nginx, ports: [{containerPort: 8080}]}]}
"""

def svc(type_, extra_spec="", annotations=None, host=None, labels=None, name="web", selector="app: web"):
    s = f"apiVersion: v1\nkind: Service\nmetadata:\n  name: {name}\n  namespace: demo\n"
    if labels: s += "  labels: {" + labels + "}\n"
    if annotations: s += "  annotations:\n" + "".join(f"    {k}: \"{v}\"\n" for k, v in annotations.items())
    s += f"spec:\n  type: {type_}\n  selector: {{{selector}}}\n  ports: [{{port: 80, targetPort: 8080}}]\n" + extra_spec
    if host: s += f"status:\n  loadBalancer:\n    ingress: [{{hostname: {host}}}]\n"
    return s

def ingress(cls_ann, host=None, tls=False, extra_ann=None):
    a = dict(cls_ann); a.update(extra_ann or {})
    s = "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: web\n  namespace: demo\n  annotations:\n"
    s += "".join(f"    {k}: \"{v}\"\n" for k, v in a.items())
    s += "spec:\n" + ("  tls: [{hosts: [app.exemplo.test]}]\n" if tls else "")
    s += "  rules:\n  - host: app.exemplo.test\n    http:\n      paths:\n      - {path: /, pathType: Prefix, backend: {service: {name: web, port: {number: 80}}}}\n"
    if host: s += f"status:\n  loadBalancer:\n    ingress: [{{hostname: {host}}}]\n"
    return s

def netpol(restrictive):
    rule = "  ingress:\n  - from: [{podSelector: {matchLabels: {app: gateway}}}]\n" if restrictive else "  ingress:\n  - {}\n"
    return ("apiVersion: networking.k8s.io/v1\nkind: NetworkPolicy\nmetadata: {name: np, namespace: demo}\n"
            "spec:\n  podSelector: {matchLabels: {app: web}}\n  policyTypes: [Ingress]\n" + rule)

def lb(name, dns, scheme, sgs):
    return {"LoadBalancerName": name, "DNSName": dns, "Scheme": scheme, "SecurityGroups": sgs}

def sg(gid, cidrs, lo=80, hi=443):
    return {"GroupId": gid, "IpPermissions": [{"IpProtocol": "tcp", "FromPort": lo, "ToPort": hi,
            "IpRanges": [{"CidrIp": c} for c in cidrs], "Ipv6Ranges": []}]}

def node(public, sgs):
    n = {"InstanceId": "i-0abc", "SecurityGroupIds": sgs}
    if public: n["PublicIpAddress"] = "203.0.113.10"
    return n

NGX = svc("LoadBalancer", labels="app.kubernetes.io/name: ingress-nginx", name="ingress-nginx-controller",
          selector="app.kubernetes.io/name: ingress-nginx", host="ngx.elb.example.test")
NGX_CLOUD = {"LoadBalancers": [lb("ngx", "ngx.elb.example.test", "internet-facing", ["sg-ngx"])],
             "SecurityGroups": [sg("sg-ngx", ["0.0.0.0/0"])]}

S = [  # (id, manifests, cloud|None, esperado)
 ("01-clusterip-netpol-restritiva", [DEPLOY, svc("ClusterIP"), netpol(True)], None, "small"),
 ("02-clusterip-sem-netpol", [DEPLOY, svc("ClusterIP")], None, "controlled"),
 ("03-clusterip-netpol-permissiva", [DEPLOY, svc("ClusterIP"), netpol(False)], None, "controlled"),
 ("04-lb-aberto-confirmado-nuvem", [DEPLOY, svc("LoadBalancer", host="a.elb.example.test")],
  {"LoadBalancers": [lb("a", "a.elb.example.test", "internet-facing", ["sg-a"])], "SecurityGroups": [sg("sg-a", ["0.0.0.0/0"])]}, "open"),
 ("05-lb-interno-confirmado-nuvem", [DEPLOY, svc("LoadBalancer", annotations={"service.beta.kubernetes.io/aws-load-balancer-internal": "true"}, host="b.elb.example.test")],
  {"LoadBalancers": [lb("b", "b.elb.example.test", "internal", ["sg-b"])], "SecurityGroups": [sg("sg-b", ["10.0.0.0/8"])]}, "controlled"),
 ("06-lb-allowlist-confirmada", [DEPLOY, svc("LoadBalancer", "  loadBalancerSourceRanges: [\"198.51.100.0/24\"]\n", host="c.elb.example.test")],
  {"LoadBalancers": [lb("c", "c.elb.example.test", "internet-facing", ["sg-c"])], "SecurityGroups": [sg("sg-c", ["198.51.100.0/24"])]}, "controlled"),
 ("07-lb-allowlist-no-manifesto-mas-nuvem-aberta", [DEPLOY, svc("LoadBalancer", "  loadBalancerSourceRanges: [\"198.51.100.0/24\"]\n", host="d.elb.example.test")],
  {"LoadBalancers": [lb("d", "d.elb.example.test", "internet-facing", ["sg-d"])], "SecurityGroups": [sg("sg-d", ["0.0.0.0/0"])]}, "open"),
 ("08-lb-sem-fatos-de-nuvem", [DEPLOY, svc("LoadBalancer")], None, "open"),
 ("09-alb-internet-facing", [DEPLOY, svc("ClusterIP"), ingress({"alb.ingress.kubernetes.io/scheme": "internet-facing"}, host="e.elb.example.test", tls=True)],
  {"LoadBalancers": [lb("e", "e.elb.example.test", "internet-facing", ["sg-e"])], "SecurityGroups": [sg("sg-e", ["0.0.0.0/0"], 443, 443)]}, "open"),
 ("10-alb-interno-padrao", [DEPLOY, svc("ClusterIP"), ingress({"kubernetes.io/ingress.class": "alb"})], None, "controlled"),
 ("11-nginx-lb-aberto", [DEPLOY, svc("ClusterIP"), ingress({"kubernetes.io/ingress.class": "nginx"}), NGX], NGX_CLOUD, "open"),
 ("12-nginx-lb-aberto-com-allowlist", [DEPLOY, svc("ClusterIP"), ingress({"kubernetes.io/ingress.class": "nginx"}, extra_ann={"nginx.ingress.kubernetes.io/allowlist-source-range": "203.0.113.0/24"}), NGX], NGX_CLOUD, "controlled"),
 ("13-nodeport-nos-privados", [DEPLOY, svc("NodePort")],
  {"Nodes": [node(False, ["sg-n"])], "SecurityGroups": [sg("sg-n", ["0.0.0.0/0"], 30000, 32767)]}, "controlled"),
 ("14-nodeport-nos-publicos-sg-aberto", [DEPLOY, svc("NodePort")],
  {"Nodes": [node(True, ["sg-n"])], "SecurityGroups": [sg("sg-n", ["0.0.0.0/0"], 30000, 32767)]}, "open"),
 ("15-nodeport-nos-publicos-sg-restrito", [DEPLOY, svc("NodePort")],
  {"Nodes": [node(True, ["sg-n"])], "SecurityGroups": [sg("sg-n", ["198.51.100.0/24"], 30000, 32767)]}, "controlled"),
 ("16-nlb-controlador-aws-padrao-interno", [DEPLOY, svc("LoadBalancer", annotations={"service.beta.kubernetes.io/aws-load-balancer-type": "external"})], None, "controlled"),
]
for sid, mans, cloud, exp in S:
    d = ROOT / sid; d.mkdir(parents=True)
    (d / "manifests.yaml").write_text("\n---\n".join(mans))
    if cloud: (d / "cloud.json").write_text(json.dumps(cloud, indent=2))
    (d / "expected.json").write_text(json.dumps({"system_exposure": exp}))
print(len(S), "cenários gerados")
