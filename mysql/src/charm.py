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
from ops.model import ActiveStatus
from ops.framework import StoredState
from ops.pebble import Layer

logger = logging.getLogger(__name__)

MYSQL_PORT = 3306


class MysqlCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.port = MYSQL_PORT
        self.framework.observe(self.on.mysql_pebble_ready, self._on_config_changed)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        logging.info("hello")

    def _on_config_changed(self, event):
        """(Re)Configure mysql pebble layer specification.
        A new mysql pebble layer specification is set only if it is
        different from the current specification.
        """
        logger.debug("Running config changed handler")
        container = self.unit.get_container("mysql")

        # Build layer
        # layers = mysqlLayers(self.config)
        mysql_layer = self.mysql_layer_2()
        plan = container.get_plan()
        service_changed = plan.services != mysql_layer.services
        if service_changed:
            container.add_layer("mysql", mysql_layer, combine=True)

        if service_changed:
            container.stop("mysql")
            container.start("mysql")
            logger.info("Restarted mysql container")

        self.unit.status = ActiveStatus()

        # self._on_update_status(event)
        logger.debug("Finished config changed handler")

    def mysql_layer_2(self):
        layer_spec = {
            "summary": "MySQL layer",
            "description": "Pebble layer configuration for replicated mysql",
            "services": {
                "mysql": {
                    "override": "replace",
                    "summary": "mysql daemon",
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
        return Layer(layer_spec)

if __name__ == "__main__":
    main(MysqlCharm)
