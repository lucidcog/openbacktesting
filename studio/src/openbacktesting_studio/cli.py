"""Launch Studio on loopback and let the browser choose a trusted workspace."""

import argparse
import socket
import sys
import webbrowser
from pathlib import Path


def bind_socket(host="127.0.0.1", port=0):
    if host not in {"127.0.0.1", "::1"}:
        raise ValueError("Only loopback addresses are supported")
    sock = socket.socket(socket.AF_INET6 if host == "::1" else socket.AF_INET)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(128)
    except BaseException:
        sock.close()
        raise
    return sock


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument(
        "result", nargs="?", type=Path, help="Result file after the view subcommand"
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Strategy interpreter with compatible Studio installed",
    )
    parser.add_argument(
        "--port", type=int, default=8765, help="Stable browser origin; use 0 for an ephemeral port"
    )
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args(argv)
    readonly = args.workspace == Path("view")
    if readonly and args.result is None:
        parser.error("view requires a result file")
    if not readonly and args.result is not None:
        parser.error("Unexpected second workspace argument")
    cache = None
    try:
        sock = bind_socket(port=args.port)
    except (OSError, ValueError) as error:
        parser.exit(2, f"Cannot bind Studio: {error}\n")
    try:
        import uvicorn

        from openbacktesting_studio.host import create_app

        origin = f"http://127.0.0.1:{sock.getsockname()[1]}"
        viewer = None
        if readonly:
            import tempfile
            import zipfile

            from openbacktesting_studio.artifacts import import_container, import_portfolio

            cache_root = Path.home() / ".cache/openbacktesting/studio"
            cache_root.mkdir(parents=True, exist_ok=True)
            cache = tempfile.TemporaryDirectory(dir=cache_root)
            viewer = Path(cache.name) / "result"
            importer = import_container if zipfile.is_zipfile(args.result) else import_portfolio
            importer(args.result, viewer)
        app = create_app(
            None if readonly else args.workspace,
            origin=origin,
            python=args.python,
            readonly=readonly,
            viewer=viewer,
            choose_workspace=not readonly,
        )
        url = origin + "/#token=" + app.state.startup_token
        print(f"OpenBacktesting Studio: {url}", flush=True)
        print(
            "Run only trusted local Python code. The worker is not a security sandbox.", flush=True
        )
        config = uvicorn.Config(app, access_log=False, log_level="warning")
        server = uvicorn.Server(config)
        if not args.no_open:
            import threading

            threading.Timer(0.5, lambda: webbrowser.open(url)).start()
        server.run(sockets=[sock])
    finally:
        sock.close()
        if cache:
            cache.cleanup()


if __name__ == "__main__":
    main()
