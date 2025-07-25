# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# neuro-san SDK Software in commercial settings.
#
# END COPYRIGHT
from typing import Dict
from typing import List

from logging import getLogger
from logging import Logger
from math import gcd as greatest_common_divisor
from threading import Thread
from time import sleep
from time import time

from neuro_san.internals.network_providers.agent_network_storage import AgentNetworkStorage
from neuro_san.service.main_loop.server_status import ServerStatus
from neuro_san.service.watcher.interfaces.startable import Startable
from neuro_san.service.watcher.interfaces.storage_updater import StorageUpdater
from neuro_san.service.watcher.registries.registry_storage_updater import RegistryStorageUpdater


# pylint: disable=too-many-instance-attributes
class StorageWatcher(Startable):
    """
    Class implementing periodic server updates
    by watching agent files and manifest file itself
    and other changes to AgentNetworkStorage instances.
    """
    def __init__(self,
                 network_storage_dict: Dict[str, AgentNetworkStorage],
                 manifest_path: str,
                 manifest_update_period_in_seconds: int,
                 server_status: ServerStatus):
        """
        Constructor.

        :param network_storage_dict: A dictionary of string (descripting scope) to
                    AgentNetworkStorage instance which keeps all the AgentNetwork instances
                    of a particular grouping.
        :param manifest_path: file path to server manifest file
        :param manifest_update_period_in_seconds: update period in seconds
        :param server_status: server status to register the state of updater
        """
        self.network_storage_dict: Dict[str, AgentNetworkStorage] = network_storage_dict
        self.logger: Logger = getLogger(self.__class__.__name__)
        self.updater_thread = Thread(target=self._run, daemon=True)

        self.storage_updaters: List[StorageUpdater] = [
            RegistryStorageUpdater(network_storage_dict, manifest_update_period_in_seconds, manifest_path),
            # We will eventually have more here
        ]

        self.update_period_in_seconds: int = self.compute_update_period_in_seconds(self.storage_updaters)

        self.server_status: ServerStatus = server_status
        self.keep_running: bool = True

    @staticmethod
    def compute_update_period_in_seconds(storage_updaters: List[StorageUpdater]) -> int:
        """
        :param storage_updaters: A list of StorageUpdaters each with their own updating
                    timing needs.
        :return: A greatest common divisor of everything in the list, or 0
                if collectively everyone says there is nothing to do.
        """
        # Figure out what the top-level update period should be.
        update_periods: List[int] = []
        for storage_updater in storage_updaters:
            update_period: int = storage_updater.get_update_period_in_seconds()
            if update_period > 0:
                # Anybody whose update period is 0 doesn't count.
                update_periods.append(update_period)

        # If we have nobody, then we shouldn't even run.
        # Luckily greatest_common_divisor() returns 0 for an empty list.
        update_period_in_seconds: int = greatest_common_divisor(*update_periods)
        return update_period_in_seconds

    def start(self):
        """
        Start running periodic StorageUpdaters.
        """
        self.logger.info("Starting StorageWatcher with %d seconds period",
                         self.update_period_in_seconds)

        for storage_updater in self.storage_updaters:
            storage_updater.start()

        self.updater_thread.start()

    def _run(self):
        """
        Function runs manifest file update cycle.
        """
        if self.update_period_in_seconds <= 0:
            # We should not run at all.
            return

        # Initial value entering the loop
        sleep_for_seconds: float = self.update_period_in_seconds
        while self.keep_running:

            self.server_status.updater.set_status(True)

            sleep(sleep_for_seconds)

            # Snap the same time so all updaters get the same sense
            # of the interval.
            time_now_in_seconds: float = time()
            for storage_updater in self.storage_updaters:
                if storage_updater.needs_updating(time_now_in_seconds):
                    storage_updater.update_storage()

            # See how long it took to update everyone.
            elapsed_time_in_seconds: float = time() - time_now_in_seconds

            # sleep() for just the right amount of time for next time around.
            # If it took longer than one cycle, then yield the cpu at least.
            sleep_for_seconds = max(self.update_period_in_seconds - elapsed_time_in_seconds, 0)

    def stop(self):
        """
        Stop running periodic StorageUpdaters.
        """
        self.logger.info("Stopping StorageWatcher with %d seconds period",
                         self.update_period_in_seconds)

        self.keep_running = False

        # Do this all in opposite order from start()

        # Wait for the thread to finish
        self.updater_thread.join()

        for storage_updater in self.storage_updaters:
            storage_updater.stop()
