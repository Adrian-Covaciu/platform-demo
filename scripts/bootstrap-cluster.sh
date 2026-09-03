#!/bin/bash
set -euo pipefail

CLUSTER_NAME=platform-demo

# Create Kind cluster (guarded — kind create cluster fails if it already exists)
if ! kind get clusters | grep -qx "$CLUSTER_NAME"; then
  kind create cluster --config "$(dirname "$0")/kind-config.yml"
fi

# Add Traefik Helm repository
helm repo add traefik https://helm.traefik.io/traefik
helm repo update

# Install Traefik configured for kind port-mapping (helm upgrade --install is already idempotent)
helm upgrade --install traefik traefik/traefik \
  --namespace traefik-ingress \
  --create-namespace \
  --set ports.web.hostPort=80 \
  --set ports.websecure.hostPort=443 \
  --set-string nodeSelector.ingress-ready=true \
  --set "tolerations[0].key=node-role.kubernetes.io/control-plane" \
  --set "tolerations[0].operator=Exists" \
  --set "tolerations[0].effect=NoSchedule"

# Install ArgoCD (namespace guarded, apply is idempotent)
if ! kubectl get namespace argocd >/dev/null 2>&1; then
  kubectl create namespace argocd
fi
kubectl apply -n argocd --server-side --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

echo "Waiting for ArgoCD pods to be ready..."
kubectl wait --for=condition=Ready pod --all -n argocd --timeout=300s

echo
echo "ArgoCD is ready. Username: admin"
echo "Get the initial admin password with:"
echo "kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"