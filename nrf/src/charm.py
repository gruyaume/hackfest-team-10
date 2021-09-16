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


class NrfCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.nrf_pebble_ready, self._on_nrf_pebble_ready)
        self.framework.observe(self.on.install, self._on_install)

    def _on_install(self, event):
        namespace_file = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
        with open(namespace_file, "r") as f:
            namespace = f.read().strip()
        kubernetes = Kubernetes(namespace=namespace)
        service_ports = [("nrf1", 80, 80, "TCP"), ("nrf2", 9090, 9090, "TCP")]
        kubernetes.set_service_port(service_name="nrf", app_name="nrf", service_ports=service_ports)

    def _on_nrf_pebble_ready(self, event):
        container_name = "nrf"
        container = self.unit.get_container(container_name)
        pebble_layer = {
            "summary": "nrf layer",
            "description": "pebble config layer for nrf",
            "services": {
                "nrf": {
                    "override": "replace",
                    "summary": "nrf",
                    "command": "/bin/bash /openair-nrf/bin/entrypoint.sh /openair-nrf/bin/oai_nrf -c /openair-nrf/etc/nrf.conf -o",
                    "environment": {
                        "INSTANCE": "0",
                        "PID_DIRECTORY": "/var/run",
                        "NRF_INTERFACE_NAME_FOR_SBI": "eth0",
                        "NRF_INTERFACE_PORT_FOR_SBI": "80",
                        "NRF_INTERFACE_HTTP2_PORT_FOR_SBI": "9090",
                        "NRF_API_VERSION": "v1"
                    },
                }
            },
        }
        container.add_layer(container_name, pebble_layer, combine=True)
        container.start("nrf")
        self.unit.status = WaitingStatus("Waiting 30 seconds for the service to start")
        time.sleep(30)
        self.unit.status = ActiveStatus()


if __name__ == "__main__":
    main(NrfCharm)
