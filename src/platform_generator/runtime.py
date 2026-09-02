from .imports import k8s
from .workload import K8sWorkload


class Worker(K8sWorkload):
    def __init__(self, scope, id, *, component, namespace):
        super().__init__(scope, id, component=component, namespace=namespace)
        k8s.KubeDeployment(self, "deployment", metadata=k8s.ObjectMeta(name=component.name, namespace=self.namespace), spec=k8s.DeploymentSpec(
            replicas=component.replicas,
            selector=k8s.LabelSelector(match_labels=self.labels),
            template=k8s.PodTemplateSpec(
                metadata=k8s.ObjectMeta(labels=self.labels),
                spec=k8s.PodSpec(containers=[self.container]),
            ),
        ))

class Api(K8sWorkload):
    def __init__(self, scope, id, *, component, namespace):
        super().__init__(scope, id, component=component, namespace=namespace)
        container = k8s.Container(
            name=self.container.name,
            image=self.container.image,
            ports=[k8s.ContainerPort(container_port=component.port)],
        )

        k8s.KubeDeployment(self, "deployment", metadata=k8s.ObjectMeta(name=component.name, namespace=self.namespace), spec=k8s.DeploymentSpec(
            replicas=component.replicas,
            selector=k8s.LabelSelector(match_labels=self.labels),
            template=k8s.PodTemplateSpec(
                metadata=k8s.ObjectMeta(labels=self.labels),
                spec=k8s.PodSpec(containers=[container]),
            ),
        ))

        k8s.KubeService(self, "service", metadata=k8s.ObjectMeta(name=component.name, namespace=self.namespace), spec=k8s.ServiceSpec(
                type="ClusterIP",
                ports=[k8s.ServicePort(port=component.port, target_port=k8s.IntOrString.from_number(component.port))],
                selector=self.labels,
            ),
        )

class CronJob(K8sWorkload):
    def __init__(self, scope, id, *, component, namespace):
        super().__init__(scope, id, component=component, namespace=namespace)
        container = k8s.Container(
            name=self.container.name,
            image=self.container.image,
            ports=[k8s.ContainerPort(container_port=component.port)],
        )

        k8s.KubeCronJob(self, "cronjob", metadata=k8s.ObjectMeta(name=component.name, namespace=self.namespace), spec=k8s.CronJobSpec(
            schedule=component.schedule,
                successful_jobs_history_limit=3,
                failed_jobs_history_limit=12,
                job_template=k8s.JobTemplateSpec(
                    spec=k8s.JobSpec(
                        template=k8s.PodTemplateSpec(
                            metadata=k8s.ObjectMeta(labels=self.labels),
                            spec=k8s.PodSpec(
                                restart_policy="OnFailure",
                                containers=[container]
                            )
                        )
                    )
                )
        ))

