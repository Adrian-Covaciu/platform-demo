import pytest
from cdk8s import App

from platform_generator.loader import load_retailers
from platform_generator.workload import K8sWorkload


def _find_component(service_name, component_name):
    for retailer in load_retailers():
        for service in retailer.services:
            if service.name == service_name:
                for component in service.components:
                    if component.name == component_name:
                        return component
    raise LookupError(f"{service_name}/{component_name} not found in registry")


def test_labels_and_container_from_real_http_component():
    component = _find_component("web", "http")
    workload = K8sWorkload(App(), component.name, component=component)

    assert workload.labels == {"app": component.name}
    assert workload.container.name == component.name
    assert workload.container.image == component.image
    assert workload.container.ports is None


def test_labels_and_container_from_real_worker_component():
    component = _find_component("gha", "worker")
    workload = K8sWorkload(App(), component.name, component=component)

    assert workload.labels == {"app": component.name}
    assert workload.container.name == component.name
    assert workload.container.image == component.image
    assert workload.container.ports is None


def test_duplicate_sibling_id_raises():
    component = _find_component("web", "http")
    app = App()
    K8sWorkload(app, "dup", component=component)

    with pytest.raises(RuntimeError):
        K8sWorkload(app, "dup", component=component)
