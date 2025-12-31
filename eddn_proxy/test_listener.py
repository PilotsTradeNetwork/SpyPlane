#!/usr/bin/env python3
"""
Test listener for EDDN proxy.
Connects to the local proxy and dumps all received events to a file.
Can be run in multiple instances with different filenames to test proxy functionality.
"""

import argparse
import sys
import time
import zlib
from pathlib import Path

import simplejson
import zmq


def run_test_listener(output_file: str):
    """Run a test listener that connects to the proxy and dumps events to a file"""
    proxy_url = "ipc:///tmp/eddn"
    dump_file_path = Path(output_file)
    
    # Ensure directory exists
    dump_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all messages
    subscriber.setsockopt(zmq.RCVTIMEO, 600000)  # 10 minute timeout
    
    print(f"Test listener started. Connecting to proxy at {proxy_url}")
    print(f"Dumping events to {dump_file_path}")
    sys.stdout.flush()
    
    continue_listening = True
    dump_file = None
    
    try:
        # Open file for appending (preserves data across reconnections)
        dump_file = dump_file_path.open("a")
        
        while continue_listening:
            try:
                subscriber.connect(proxy_url)
                print(f"Connected to proxy at {proxy_url}")
                sys.stdout.flush()
                
                while continue_listening:
                    try:
                        message = subscriber.recv()
                        
                        if not message:
                            subscriber.disconnect(proxy_url)
                            break
                        
                        # Decompress and parse message
                        try:
                            decompressed = zlib.decompress(message)
                            json_data = simplejson.loads(decompressed)
                            
                            # Write to file
                            dump_file.write(simplejson.dumps(json_data) + "\n")
                            dump_file.flush()
                            
                            # Print a brief summary to stdout for monitoring
                            event_type = json_data.get("$schemaRef", "unknown")
                            print(f"Received event: {event_type}")
                            sys.stdout.flush()
                            
                        except zlib.error as e:
                            print(f"Error decompressing message: {e}", file=sys.stderr)
                            sys.stderr.flush()
                        except Exception as e:
                            print(f"Error parsing message: {e}", file=sys.stderr)
                            sys.stderr.flush()
                            
                    except zmq.Again:
                        # Timeout - this is normal, just continue
                        continue
                        
            except zmq.ZMQError as e:
                print(f"ZMQ error: {e}", file=sys.stderr)
                sys.stderr.flush()
                try:
                    subscriber.disconnect(proxy_url)
                except Exception:
                    pass
                if dump_file:
                    dump_file.close()
                    dump_file = None
                time.sleep(5)  # Wait before reconnecting
                if continue_listening:
                    dump_file = dump_file_path.open("a")  # Append mode for reconnection
            except KeyboardInterrupt:
                print("\nShutting down...")
                continue_listening = False
            except Exception as e:
                print(f"Unexpected error: {e}", file=sys.stderr)
                sys.stderr.flush()
                try:
                    subscriber.disconnect(proxy_url)
                except Exception:
                    pass
                if dump_file:
                    dump_file.close()
                    dump_file = None
                time.sleep(5)  # Wait before reconnecting
                if continue_listening:
                    dump_file = dump_file_path.open("a")  # Append mode for reconnection
                    
    finally:
        # Cleanup
        if dump_file:
            dump_file.close()
        try:
            subscriber.disconnect(proxy_url)
        except Exception:
            pass
        subscriber.close()
        context.term()
        print("Test listener stopped")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Test listener for EDDN proxy. Dumps all received events to a file."
    )
    parser.add_argument(
        "filename",
        help="Output filename to dump events to (will be created/opened in append mode)"
    )
    
    args = parser.parse_args()
    run_test_listener(args.filename)


if __name__ == "__main__":
    main()

