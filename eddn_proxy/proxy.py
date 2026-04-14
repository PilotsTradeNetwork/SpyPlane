import zmq


def run_proxy():
    context = zmq.Context()

    # 1. Frontend: Connects to the remote original source
    frontend = context.socket(zmq.XSUB)
    frontend.connect("tcp://eddn.edcd.io:9500")

    # 2. Backend: Binds to a local interface for your apps
    backend = context.socket(zmq.XPUB)
    # Using IPC is faster for local apps than TCP
    backend.bind("ipc:///tmp/eddn")

    # 3. Start the proxy (Built-in ZMQ device)
    # This blocks and automatically shuttles data between sockets
    zmq.proxy(frontend, backend)


if __name__ == "__main__":
    run_proxy()
