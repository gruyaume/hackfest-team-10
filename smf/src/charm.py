#!/usr/bin/env python3
# Copyright 2021 Guillaume
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, WaitingStatus
from kubernetes_api import Kubernetes
import time

logger = logging.getLogger(__name__)


class SmfCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.smf_pebble_ready, self._on_smf_pebble_ready)
        self.framework.observe(self.on.install, self._on_install)

    def _on_install(self, event):
        namespace_file = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
        with open(namespace_file, "r") as f:
            namespace = f.read().strip()
        kubernetes = Kubernetes(namespace=namespace)
        service_ports = [("smf1", 8805, 8805, "UDP"), ("smf2", 80, 80, "TCP"), ("smf3", 9090, 9090, "TCP")]
        kubernetes.set_service_port(service_name="smf", app_name="smf", service_ports=service_ports)

    def _on_smf_pebble_ready(self, event):
        container_name = "smf"
        container = self.unit.get_container(container_name)
        pebble_layer = {
            "summary": "smf layer",
            "description": "pebble config layer for smf",
            "services": {
                "smf": {
                    "override": "replace",
                    "summary": "smf",
                    "command": "/bin/bash /openair-smf/bin/entrypoint.sh /openair-smf/bin/oai_smf -c /openair-smf/etc/smf.conf -o",
                    "environment": {
                        "INSTANCE": "0",
                        "PID_DIRECTORY": "/var/run",
                        "SMF_INTERFACE_NAME_FOR_N4": "eth0",
                        "SMF_INTERFACE_NAME_FOR_SBI": "eth0",
                        "SMF_INTERFACE_PORT_FOR_SBI": "80",
                        "SMF_INTERFACE_HTTP2_PORT_FOR_SBI": "9090",
                        "SMF_API_VERSION": "v1",
                        "DEFAULT_DNS_IPV4_ADDRESS": "192.168.18.129",
                        "DEFAULT_DNS_SEC_IPV4_ADDRESS": "192.168.18.129",
                        "REGISTER_NRF": "yes",
                        "DISCOVER_UPF": "yes",
                        "USE_FQDN_DNS": "yes",
                        "AMF_IPV4_ADDRESS": "127.0.0.1",
                        "AMF_PORT": "80",
                        "AMF_API_VERSION": "v1",
                        "AMF_FQDN": "amf",
                        "UDM_IPV4_ADDRESS": "127.0.0.1",
                        "UDM_PORT": "80",
                        "UDM_API_VERSION": "v1",
                        "UDM_FQDN": "localhost",
                        "NRF_IPV4_ADDRESS": "127.0.0.1",
                        "NRF_PORT": "80",
                        "NRF_API_VERSION": "v1",
                        "NRF_FQDN": "nrf",
                        "UPF_IPV4_ADDRESS": "127.0.0.1",
                        "UPF_FQDN_0": "upf"
                    },
                }
            },
        }
        container.add_layer(container_name, pebble_layer, combine=True)
        container.start("smf")
        self.unit.status = WaitingStatus("Waiting 30 seconds for the service to start")
        time.sleep(30)
        self.unit.status = ActiveStatus()

if __name__ == "__main__":
    main(SmfCharm)
