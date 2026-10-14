# OpenBacktesting Studio

An optional local web workspace for the OpenBacktesting Python framework.
Core-only users do not install Studio or its web dependencies. This package supplies
its own loopback host, prebuilt UI, chart library and editor worker.

- [Illustrated getting started guide](https://docs.openbacktesting.com/studio/)
- [Installation and workflow](docs/guide.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Developer builds](docs/development.md)
- [Versioned host protocol](docs/protocol.md)
- [Chart source and licenses](vendor-metadata/README.md)

Install Studio 0.1.0 into a Python 3.12–3.14 environment:

```sh
python -m pip install openbacktesting-studio==0.1.0
openbacktesting-studio /path/to/strategies
```

Installation includes a compatible core (`openbacktesting>=0.2.1,<0.3`).
Independent wheel and sdist artifacts include the compiled interface; end-user installation
requires no Node or CDN. The verified platform is macOS with Python 3.12–3.14 compatibility
checks; platform verification details are recorded with the implementing OpenSpec change.
