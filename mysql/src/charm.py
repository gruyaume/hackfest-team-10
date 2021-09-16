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
import time
from pathlib import Path

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, WaitingStatus
from kubernetes_api import Kubernetes

logger = logging.getLogger(__name__)

MYSQL_PORT = 3306


class MysqlCharm(CharmBase):

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.mysql_pebble_ready, self._on_mysql_pebble_ready)
        self.framework.observe(self.on.install, self._on_install)

    def _on_install(self, event):
        namespace_file = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
        with open(namespace_file, "r") as f:
            namespace = f.read().strip()
        kubernetes_api = Kubernetes(namespace)
        kubernetes_api.set_service_port(service_name="mysql", app_name="myqsql", port=3306)

    def _on_mysql_pebble_ready(self, event):
        container_name = "mysql"
        container = self.unit.get_container(container_name)
        pebble_layer = {
            "summary": "mysql layer",
            "description": "pebble config layer for mysql",
            "services": {
                "mysql": {
                    "override": "replace",
                    "summary": "mysql",
                    "command": "docker-entrypoint.sh mysqld",
                    "environment": {
                        "MYSQL_ALLOW_EMPTY_PASSWORD": "true",
                        "MYSQL_ROOT_PASSWORD": "linux",
                        "MYSQL_PASSWORD": "test",
                        "MYSQL_USER": "test",
                        "MYSQL_DATABASE": "oai_db",
                    }
                }
            }
        }
        container.add_layer(container_name, pebble_layer, combine=True)
        container.push(
            "/docker-entrypoint-initdb.d/db.sql", Path("templates/db.sql").read_text()
        )
        container.start("mysql")
        self.unit.status = WaitingStatus("Waiting 30 seconds for the service to start")
        time.sleep(30)
        self.unit.status = ActiveStatus()


if __name__ == "__main__":
    main(MysqlCharm)
