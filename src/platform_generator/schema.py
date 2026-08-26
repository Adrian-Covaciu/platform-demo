import yaml
from models import *
import os


def load_yaml_file(path):
    with open(path, "r") as f:
        return yaml.safe_load(f.read())


def load_component(service_path, name):
    return load_yaml_file(os.path.join(service_path, name, "component.yaml"))


def load_resources(service_path):
    shared_path = os.path.join(service_path, "shared")
    if not os.path.isdir(shared_path):
        return []
    return [
        load_yaml_file(os.path.join(shared_path, filename))
        for filename in os.listdir(shared_path)
    ]


def load_service(services_path, name):
    service_path = os.path.join(services_path, name)
    service_data = load_yaml_file(os.path.join(service_path, "service.yaml"))
    service_data["components"] = [
        load_component(service_path, component_name)
        for component_name in service_data["components"]
    ]
    service_data["resources"] = load_resources(service_path)
    return service_data


def load_retailers():
    registry_path = os.path.join(os.path.dirname(__file__), "..", "..", "registry")
    retailers_path = os.path.join(registry_path, "retailers")
    services_path = os.path.join(registry_path, "services")

    for dir in os.listdir(retailers_path):
        retailer_path = os.path.join(retailers_path, dir)
        retailer_yaml_path = os.path.join(retailer_path, "retailer.yaml")
        if os.path.isdir(retailer_path) and os.path.exists(retailer_yaml_path):
            retailer_data = load_yaml_file(retailer_yaml_path)
            retailer_data["services"] = [
                load_service(services_path, service_name)
                for service_name in retailer_data.get("services", [])
            ]
            yield retailer_data


for retailer_data in load_retailers():
    retailer = Retailer.model_validate(retailer_data)
    print(retailer.model_dump_json(indent=2))2
