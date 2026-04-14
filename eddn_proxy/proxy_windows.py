import zmq


def run_windows_proxy():
    context = zmq.Context()

    # 1. Frontend: Connect to remote source (Same as Linux)
    frontend = context.socket(zmq.XSUB)
    frontend.connect("tcp://eddn.edcd.io:9500")

    # Instead of 'ipc:///tmp/feed', use local TCP for Windows
    backend = context.socket(zmq.XPUB)
    backend.bind("tcp://127.0.0.1:5556")  # Localhost only

    print("Windows Proxy running on tcp://127.0.0.1:5556")

    # 3. Start the proxy
    zmq.proxy(frontend, backend)


if __name__ == "__main__":
    run_windows_proxy()
