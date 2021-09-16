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
import time
from kubernetes_api import Kubernetes

logger = logging.getLogger(__name__)


class UpfCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.upf_pebble_ready, self._on_upf_pebble_ready)
        self.framework.observe(self.on.install, self._on_install)

    def _on_install(self, event):
        namespace_file = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
        with open(namespace_file, "r") as f:
            namespace = f.read().strip()
        kubernetes = Kubernetes(namespace=namespace)
        service_ports = [("upf1", 8805, 8805, "UDP"), ("upf2", 2152, 2152, "UDP"), ("upf3", 5001, 5001, "UDP")]
        kubernetes.set_service_port(service_name="upf", app_name="upf", service_ports=service_ports)

    def _on_upf_pebble_ready(self, event):
        container_name = "upf"
        container = self.unit.get_container(container_name)
        pebble_layer = {
            "summary": "upf layer",
            "description": "pebble config layer for upf",
            "services": {
                "upf": {
                    "override": "replace",
                    "summary": "upf",
                    "command": "/bin/bash /openair-spgwu-tiny/bin/entrypoint.sh /openair-spgwu-tiny/bin/oai_spgwu -c /openair-spgwu-tiny/etc/spgw_u.conf -o",
                    "environment": {
                        "GW_ID": "1",
                        "MNC03": "208",
                        "MCC": "95",
                        "REALM": "3gpp.org",
                        "PID_DIRECTORY": "/var/run",
                        "SGW_INTERFACE_NAME_FOR_S1U_S12_S4_UP": "eth0",
                        "THREAD_S1U_PRIO": 98,
                        "S1U_THREADS": 1,
                        "SGW_INTERFACE_NAME_FOR_SX": "eth0",
                        "THREAD_SX_PRIO": 98,
                        "SX_THREADS": 1,
                        "PGW_INTERFACE_NAME_FOR_SGI": "eth0",
                        "THREAD_SGI_PRIO": 98,
                        "SGI_THREADS": 1,
                        "NETWORK_UE_NAT_OPTION": "yes",
                        "GTP_EXTENSION_HEADER_PRESENT": "yes",
                        "NETWORK_UE_IP": "12.1.1.0/24",
                        "SPGWC0_IP_ADDRESS": "127.0.0.1",
                        "BYPASS_UL_PFCP_RULES": "no",
                        "ENABLE_5G_FEATURES": "yes",
                        "REGISTER_NRF": "yes",
                        "USE_FQDN_NRF": "yes",
                        "NRF_IPV4_ADDRESS": "127.0.0.1",
                        "NRF_PORT": "80",
                        "NRF_API_VERSION": "v1",
                        "NRF_FQDN": "nrf",
                        "NSSAI_SST_0": 1,
                        "NSSAI_SD_0": 1,
                        "DNN_0": "oai",
                        "UPF_FQDN_5G": "upf"
                    },
                }
            },
        }
        container.add_layer(container_name, pebble_layer, combine=True)
        container.start("upf")
        self.unit.status = WaitingStatus("Waiting 30 seconds for the service to start")
        time.sleep(30)
        self.unit.status = ActiveStatus()

if __name__ == "__main__":
    main(UpfCharm)
