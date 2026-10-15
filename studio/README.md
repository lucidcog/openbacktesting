<h1>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../docs/assets/brand/wordmark-white.svg">
  <img src="../docs/assets/brand/wordmark.svg" alt="OpenBacktesting" width="300" height="36">
</picture> Studio
</h1>

An optional local web workspace for the OpenBacktesting Python framework.
Core-only users do not install Studio or its web dependencies. This package supplies
its own loopback host, prebuilt UI, chart library and editor worker.

On macOS, install and open Studio with one command:

```sh
curl -fsSL https://docs.openbacktesting.com/install-studio.sh | bash
```

The installer prepares all dependencies automatically. Reopen Studio by double-clicking
`~/Applications/OpenBacktesting Studio.command`.

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
