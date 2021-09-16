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


class AmfCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.amf_pebble_ready, self._on_amf_pebble_ready)
        self.framework.observe(self.on.install, self._on_install)

    def _on_install(self, event):
        namespace_file = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
        with open(namespace_file, "r") as f:
            namespace = f.read().strip()
        kubernetes_api = Kubernetes(namespace)
        service_ports = [("amf1", 38412, 38412, "TCP"), ("amf2", 80, 80, "TCP"), ("amf3", 9090, 9090, "TCP")]
        kubernetes_api.set_service_port(service_name="amf", app_name="amf", service_ports=service_ports)

    def _on_amf_pebble_ready(self, event):
        container_name = "amf"
        container = self.unit.get_container(container_name)
        pebble_layer = {
            "summary": "amf layer",
            "description": "pebble config layer for amf",
            "services": {
                "amf": {
                    "override": "replace",
                    "summary": "amf",
                    "command": "/bin/bash /openair-amf/bin/entrypoint.sh /openair-amf/bin/oai_amf -c /openair-amf/etc/amf.conf -o",
                    "environment": {
                        "INSTANCE": "0",
                        "PID_DIRECTORY": "/var/run",
                        "MCC": "208",
                        "MNC": "95",
                        "REGION_ID": "128",
                        "AMF_SET_ID": "1",
                        "SERVED_GUAMI_MCC_0": "208",
                        "SERVED_GUAMI_MNC_0": "95",
                        "SERVED_GUAMI_REGION_ID_0": "128",
                        "SERVED_GUAMI_AMF_SET_ID_0": "1",
                        "SERVED_GUAMI_MCC_1": "460",
                        "SERVED_GUAMI_MNC_1": "11",
                        "SERVED_GUAMI_REGION_ID_1": "10",
                        "SERVED_GUAMI_AMF_SET_ID_1": "1",
                        "PLMN_SUPPORT_MCC": "208",
                        "PLMN_SUPPORT_MNC": "95",
                        "PLMN_SUPPORT_TAC": "0xa000",
                        "SST_0": "222",
                        "SD_0": "123",
                        "SST_1": "111",
                        "SD_1": "124",
                        "AMF_INTERFACE_NAME_FOR_NGAP": "eth0",
                        "AMF_INTERFACE_NAME_FOR_N11": "eth0",
                        "SMF_INSTANCE_ID_0": "1",
                        "SMF_IPV4_ADDR_0": "0.0.0.0",
                        "SMF_HTTP_VERSION_0": "v1",
                        "SMF_FQDN_0": "localhost",
                        "SMF_INSTANCE_ID_1": "2",
                        "SMF_IPV4_ADDR_1": "0.0.0.0",
                        "SMF_HTTP_VERSION_1": "v1",
                        "SMF_FQDN_1": "localhost",
                        "NRF_IPV4_ADDRESS": "0.0.0.0",
                        "NRF_PORT": 80,
                        "NRF_API_VERSION": "v1",
                        "NRF_FQDN": "nrf",
                        "AUSF_IPV4_ADDRESS": "127.0.0.1",
                        "AUSF_PORT": 80,
                        "AUSF_API_VERSION": "v1",
                        "NF_REGISTRATION": "yes",
                        "SMF_SELECTION": "yes",
                        "USE_FQDN_DNS": "yes",
                        "MYSQL_SERVER": "mysql",
                        "MYSQL_USER": "root",
                        "MYSQL_PASS": "linux",
                        "MYSQL_DB": "oai_db",
                        "OPERATOR_KEY": "63bfa50ee6523365ff14c1f45f88737d"
                    },
                }
            },
        }
        container.add_layer(container_name, pebble_layer, combine=True)
        container.start("amf")
        self.unit.status = WaitingStatus("Waiting 30 seconds for the service to start")
        time.sleep(30)
        self.unit.status = ActiveStatus()


if __name__ == "__main__":
    main(AmfCharm)
