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

Studio is currently a source-checkout implementation, not a claimed published release.
Build instructions produce independent wheel and sdist artifacts; end-user installation
requires no Node or CDN. The verified platform is macOS with Python 3.12–3.14 compatibility
checks; platform verification details are recorded with the implementing OpenSpec change.
