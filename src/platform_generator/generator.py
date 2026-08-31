
from pathlib import Path
from cdk8s import App, Chart
from .runtime import Worker, Api, CronJob
from .loader import load_retailers
from .imports import k8s
from .models import Retailer, WorkloadType

WORKLOAD_CLASSES = {WorkloadType.API: Api, WorkloadType.WORKER: Worker, WorkloadType.CRONJOB: CronJob}


def generate_retailer(retailer: Retailer) -> None:
    outdir = f"rendered/k8s/{retailer.name}"
    app = App(outdir=outdir, output_file_extension=".yaml")
    for service in retailer.services:
        chart = Chart(app, service.name)
        k8s.KubeNamespace(chart, service.name, metadata=k8s.ObjectMeta(name=service.name))
        for component in service.components:
            WORKLOAD_CLASSES[component.workload_type](chart, component.name, component=component, namespace=service.name)
    app.synth()

    for service in retailer.services:
        rendered_file = Path(outdir) / f"{service.name}.yaml"
        rendered_file.write_text("# rendered_schema_version: 1\n" + rendered_file.read_text())


if __name__ == "__main__":
    for retailer in load_retailers():
        generate_retailer(retailer)