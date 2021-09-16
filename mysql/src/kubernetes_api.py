from kubernetes import client, config


class Kubernetes:
    def __init__(self, namespace: str):
        config.load_incluster_config()
        self.namespace = namespace
        self.v1 = client.CoreV1Api()

    def set_service_port(self, service_name: str, app_name: str, port: int, protocol: str = "TCP"):
        service_ports = [(app_name, port, port, protocol)]
        ports = [
            client.V1ServicePort(
                name=port[0], port=port[1], target_port=port[2], protocol=port[3]
            )
            for port in service_ports
        ]
        service = client.V1Service(
            api_version="v1",
            metadata=client.V1ObjectMeta(
                namespace=self.namespace,
                name=service_name,
                labels={"app.kubernetes.io/name": app_name},
            ),
            spec=client.V1ServiceSpec(
                ports=ports,
                selector={"app.kubernetes.io/name": app_name},
            ),
        )
        self.v1.delete_namespaced_service(service_name, self.namespace)
        self.v1.create_namespaced_service(self.namespace, service)
