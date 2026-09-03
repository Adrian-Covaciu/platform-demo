from constructs import Construct

from .imports import k8s
from .models import Component


class K8sWorkload(Construct):
    def __init__(self, scope: Construct, id: str, *, component: Component, namespace: str):
        super().__init__(scope, id)
        self.labels = {"app": component.name}
        self.container = k8s.Container(name=component.name, image=component.image, command=component.command)
        self.namespace = namespace
