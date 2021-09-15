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
from ops.framework import StoredState

logger = logging.getLogger(__name__)

MYSQL_PORT = 3306


class MysqlCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self._stored.set_default(mysql_initialized=False)
        self.port = MYSQL_PORT
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_config_changed(self, event):
        """Handle the config-changed event"""
        # Get the mysql container so we can configure/manipulate it
        container = self.unit.get_container("mysql")
        # Create a new config layer
        layer = self._mysql_layer()

        if container.can_connect():
            # Get the current config
            services = container.get_plan().to_dict().get("services", {})
            # Check if there are any changes to services
            if services != layer["services"]:
                # Changes were made, add the new layer
                container.add_layer("mysql", layer, combine=True)
                logging.info("Added updated layer 'mysql' to Pebble plan")
                # Restart it and report a new status to Juju
                container.restart("mysql")
                logging.info("Restarted mysql service")
            # All is well, set an ActiveStatus
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("waiting for Pebble in workload container")

    def _mysql_layer(self):
        """Returns a Pebble configration layer for Gosherve"""
        return {
            "summary": "mysql layer",
            "description": "pebble config layer for mysql",
            "services": {
                "mysql": {
                    "override": "replace",
                    "summary": "mysql",
                    "command": "/usr/local/bin/docker-entrypoint.sh",
                    "startup": "enabled",
                    "environment": {
                        "MYSQL_USER": "test",
                        "MYSQL_PASSWORD": "test",
                        "MYSQL_DATABASE": "oai_db",
                        "MYSQL_ROOT_PASSWORD": "linux",
                        "MYSQL_ALLOW_EMPTY_PASSWORD": "true"
                    }
                }
            },
        }

if __name__ == "__main__":
    main(MysqlCharm)
