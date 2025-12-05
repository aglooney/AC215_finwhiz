# Deployment quickstart

Minimal steps to build images and deploy Kubernetes.

1) Enter Docker shell (run from repo root):
```bash
cd src/deployment
sh docker-shell.sh
```

2) Build & publish images:
```bash
cd deploy_images
pulumi up --stack dev --refresh -y
```

3) Deploy Kubernetes:
```bash
cd ../deploy_k8s
pulumi up --stack dev --refresh -y
```

4) Check status:
```bash
kubectl get pods -n finwhiz-namespace
kubectl get ingress -n finwhiz-namespace
```

Teardown:
```bash
pulumi destroy --stack dev -y
```
