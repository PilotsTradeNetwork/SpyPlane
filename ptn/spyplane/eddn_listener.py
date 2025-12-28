import logging
import sys
import threading
import time
import zlib
from pathlib import Path
from typing import Optional

import simplejson
import zmq

from ptn.spyplane.bot_registry import get_bot
from ptn.spyplane.constants import EDDN_URL, log, log_exception
from ptn.spyplane.database.systems_repository import SystemsRepository
from ptn.spyplane.helpers.journal_helper import JournalHelper
from ptn.spyplane.services.scout_recording_service import ScoutRecordingService


class EddnListenerThread(threading.Thread):
    """Thread that listens to EDDN stream and dumps events to a file"""

    def __init__(self, dump_file: Optional[Path] = None):
        threading.Thread.__init__(self)
        self.name = "EDDN Listener"
        self.eddn_url = EDDN_URL
        self.context = zmq.Context()
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b"")
        self.subscriber.setsockopt(zmq.RCVTIMEO, 600000)  # 10 minute timeout
        self.continue_listening = True
        self.dump_file_path = dump_file or Path("./workspace/eddn_events.jsonl")
        self.dump_file: Optional[object] = None
        self.journal_helper = JournalHelper()
        self.systems_repo = SystemsRepository()
        self.record_service = ScoutRecordingService()

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

                    # Filter events - only dump FSDJump, Location, and CarrierJump events from tracked systems
                    if self.journal_helper.is_target_event(json_data):
                        self.dump_file.write(simplejson.dumps(json_data) + "\n")
                        self.dump_file.flush()

                        # Process the event: record scout and delete message
                        self._process_eddn_event(json_data)

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

    def _process_eddn_event(self, json_data: dict) -> None:
        """Process an EDDN event: record scout and delete Discord message"""
        try:
            # Extract system name from event
            message = json_data.get("message", {})
            star_system = message.get("StarSystem")

            if not star_system:
                log("EDDN event missing StarSystem field")
                return

            # Schedule async operations on the bot's event loop
            try:
                bot = get_bot()
                if hasattr(bot, "loop") and bot.loop and bot.loop.is_running():
                    bot.loop.create_task(self._handle_eddn_scout(star_system))
                else:
                    log("Bot event loop not available for EDDN event processing")
            except RuntimeError:
                log("Bot not registered yet for EDDN event processing")
        except Exception as e:
            log_exception("Error processing EDDN event", e)

    async def _handle_eddn_scout(self, system_name: str) -> None:
        """Handle scout recording and message deletion for EDDN event"""
        try:
            # Get message_id from scout_systems_posted BEFORE recording (record_reaction removes it)
            message_id = await self.systems_repo.get_message_id(system_name)

            # Record the scout with EDDN as username and 0 as userid
            await self.record_service.record_reaction(system_name, "EDDN", 0)

            # Delete the Discord message if we have message_id
            bot = get_bot()
            if message_id and bot.channel:
                try:
                    message = await bot.channel.fetch_message(message_id)
                    if not message.pinned:
                        await message.delete()
                        log(f"Deleted Discord message {message_id} for system {system_name} from EDDN event")
                    else:
                        log(f"Message {message_id} is pinned, not deleting")
                except Exception as e:
                    log(f"Error deleting message {message_id} for system {system_name}: {e}")
            elif not message_id:
                log(f"No message_id found for system {system_name} in scout_systems_posted")
            elif not bot.channel:
                log(f"Bot channel not available for deleting message for system {system_name}")
        except Exception as e:
            log_exception("Error handling EDDN scout", e)

    def stop(self):
        """Stop the listener thread"""
        self.continue_listening = False
        if self.dump_file:
            self.dump_file.close()


# Thread instance - created lazily to avoid circular imports
_eddn_listener_thread: Optional[EddnListenerThread] = None


def get_eddn_listener_thread() -> EddnListenerThread:
    """Get or create the EDDN listener thread instance"""
    global _eddn_listener_thread
    if _eddn_listener_thread is None:
        _eddn_listener_thread = EddnListenerThread()
    return _eddn_listener_thread

