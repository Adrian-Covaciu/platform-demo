import os
import pytest
from src.platform_generator.loader import load_service, load_retailers


def test_real_registry_loads_without_error():
    # Walks the actual registry/ tree end-to-end. If someone adds a bad
    # reference (a service/component name with no matching directory) to
    # any real retailer.yaml or service.yaml, this is what catches it.
    list(load_retailers())

def test_unique_service_names_within_retailer():
    for retailer in load_retailers():
        seen = set()
        for service in retailer.services:
            assert service.name not in seen, f"Duplicate service name in {retailer.name}: {service.name}"
            seen.add(service.name)
