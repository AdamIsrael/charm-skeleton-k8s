#!/usr/bin/env python3

import sys

sys.path.append("lib")

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import (
    ActiveStatus,
    BlockedStatus,
    MaintenanceStatus,
    WaitingStatus,
    ModelError,
)


class SkeletonCharm(CharmBase):
    state = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        print("__init__")
        # An example of setting charm state
        # that's persistent across events
        self.state.set_default(is_started=False)

        if not self.state.is_started:
            self.state.is_started = True

        # Register all of the events we want to observe
        for event in (
            # Charm events
            self.on.config_changed,
            self.on.start,
            self.on.upgrade_charm,
        ):
            self.framework.observe(event, self)

    def _apply_spec(self, spec):
        # Only apply the spec if this unit is a leader.
        if self.framework.model.unit.is_leader():
            print("_apply_spec")
            self.framework.model.pod.set_spec(spec)
            self.state.spec = spec

    def make_pod_spec(self):
        print("make_pod_spec")
        config = self.framework.model.config

        ports = [{"name": "http", "containerPort": 80, "protocol": "TCP"}]

        spec = {
            'containers': [{
                'name': self.framework.model.app.name,
                "image": config["image"],
                "ports": ports,
            }],
        }

        return spec

    def on_config_changed(self, event):
        """Handle changes in configuration"""
        unit = self.model.unit

        new_spec = self.make_pod_spec()
        if self.state.spec != new_spec:
            self._apply_spec(new_spec)


    def on_start(self, event):
        """Called when the charm is being installed"""
        unit = self.model.unit

        new_pod_spec = self.make_pod_spec()
        self._apply_spec(new_pod_spec)

        unit.status = ActiveStatus()

    def on_upgrade_charm(self, event):
        """Upgrade the charm."""
        unit = self.model.unit

        # Mark the unit as under Maintenance.
        unit.status = MaintenanceStatus("Upgrading charm")

        self.on_install(event)

        # When maintenance is done, return to an Active state
        unit.status = ActiveStatus()


if __name__ == "__main__":
    main(SkeletonCharm)
