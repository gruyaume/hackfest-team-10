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
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, WaitingStatus

logger = logging.getLogger(__name__)


class NrfCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_config_changed(self, event):
        """Handle the config-changed event"""
        # Get the nrf container so we can configure/manipulate it
        container = self.unit.get_container("nrf")
        # Create a new config layer
        layer = self._nrf_layer()

        if container.can_connect():
            # Get the current config
            services = container.get_plan().to_dict().get("services", {})
            # Check if there are any changes to services
            if services != layer["services"]:
                # Changes were made, add the new layer
                container.add_layer("nrf", layer, combine=True)
                logging.info("Added updated layer 'nrf' to Pebble plan")
                # Restart it and report a new status to Juju
                container.stop("nrf")
                container.start("nrf")
                logging.info("Restarted nrf service")
            # All is well, set an ActiveStatus
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("waiting for Pebble in workload container")

    def _nrf_layer(self):
        """Returns a Pebble configration layer for Gosherve"""
        return {
            "summary": "nrf layer",
            "description": "pebble config layer for nrf",
            "services": {
                "nrf": {
                    "override": "replace",
                    "summary": "nrf",
                    "command": "/openair-nrf/bin/oai_nrf -c /openair-nrf/etc/nrf.conf -o",
                    "startup": "enabled",
                    "environment": {
                        "INSTANCE": "0",
                        "PID_DIRECTORY": "/var/run",
                        "NRF_INTERFACE_NAME_FOR_SBI": "eth0",
                        "NRF_INTERFACE_PORT_FOR_SBI": "80",
                        "NRF_INTERFACE_HTTP2_PORT_FOR_SBI": "9090",
                        "NRF_API_VERSION": "v1"
                    }
                }
            },
        }

if __name__ == "__main__":
    main(NrfCharm)
