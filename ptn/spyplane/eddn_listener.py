import logging
import sys
import threading
import time
import zlib
from pathlib import Path
from typing import Optional

import simplejson
import zmq

from ptn.spyplane.constants import log, log_exception
from ptn.spyplane.helpers.journal_helper import JournalHelper


class EddnListenerThread(threading.Thread):
    """Thread that listens to EDDN stream and dumps events to a file"""

    def __init__(self, dump_file: Optional[Path] = None):
        threading.Thread.__init__(self)
        self.name = "EDDN Listener"
        self.eddn_url = "tcp://eddn.edcd.io:9500"
        self.context = zmq.Context()
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b"")
        self.subscriber.setsockopt(zmq.RCVTIMEO, 600000)  # 10 minute timeout
        self.continue_listening = True
        self.dump_file_path = dump_file or Path("./workspace/eddn_events.jsonl")
        self.dump_file: Optional[object] = None
        self.journal_helper = JournalHelper()

    def run(self):
        """Main listener loop"""
        # Ensure directory exists
        self.dump_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Open file for appending (preserves data across reconnections)
        self.dump_file = self.dump_file_path.open("a")
        log(f"EDDN listener started. Dumping events to {self.dump_file_path}")

        while self.continue_listening:
            try:
                self.subscriber.connect(self.eddn_url)
                log(f"Connected to EDDN stream at {self.eddn_url}")

                while self.continue_listening:
                    message = self.subscriber.recv()

                    if not message:
                        self.subscriber.disconnect(self.eddn_url)
                        break

                    # Decompress and parse message
                    message = zlib.decompress(message)
                    json_data = simplejson.loads(message)

                    # Filter events - only dump FSDJump, Location, and CarrierJump events
                    if self.journal_helper.is_target_event(json_data):
                        self.dump_file.write(simplejson.dumps(json_data) + "\n")
                        self.dump_file.flush()

            except zmq.ZMQError as e:
                log_exception("EDDN listener ZMQ error", e)
                sys.stdout.flush()
                try:
                    self.subscriber.disconnect(self.eddn_url)
                except Exception:
                    pass
                if self.dump_file:
                    self.dump_file.close()
                    self.dump_file = None
                time.sleep(5)  # Wait before reconnecting
                # Reopen file for next connection attempt
                if self.continue_listening:
                    self.dump_file = self.dump_file_path.open("a")  # Append mode for reconnection
            except Exception as e:
                log_exception("EDDN listener unexpected error", e)
                sys.stdout.flush()
                try:
                    self.subscriber.disconnect(self.eddn_url)
                except Exception:
                    pass
                if self.dump_file:
                    self.dump_file.close()
                    self.dump_file = None
                time.sleep(5)  # Wait before reconnecting
                # Reopen file for next connection attempt
                if self.continue_listening:
                    self.dump_file = self.dump_file_path.open("a")  # Append mode for reconnection

        # Cleanup
        if self.dump_file:
            self.dump_file.close()
        log("EDDN listener stopped")

    def stop(self):
        """Stop the listener thread"""
        self.continue_listening = False
        if self.dump_file:
            self.dump_file.close()


# Global thread instance
eddn_listener_thread = EddnListenerThread()

