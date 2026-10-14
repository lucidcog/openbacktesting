---
title: Studio — install and launch
description: Install and open Studio on macOS with one command. The installer prepares everything automatically and creates a double-click launcher.
---

# Install and launch

On **macOS**, open Terminal and paste:

```sh
curl -fsSL https://docs.openbacktesting.com/install-studio.sh | bash
```

The installer downloads Studio, prepares its dependencies, and opens it in your browser. You do not need to install Python, Node.js, or Git yourself. The first installation takes a few minutes and needs an internet connection.

Choose a workspace when Studio opens. The installer includes example strategies so you can [run your first backtest](first-backtest.md) immediately.

## Open Studio again

Double-click **OpenBacktesting Studio.command** in your home folder's **Applications** directory. Keep its Terminal window open while using Studio; press **Ctrl+C** there to stop it.

You can also start it from Terminal:

```sh
~/.local/share/openbacktesting-studio/studio
```

## Update Studio

Run the installation command again. Your example edits and workspace history are kept. If downloading or building fails, the previous installation remains available.

## Installation details

The installer currently supports **Apple Silicon and Intel Macs**. Linux and Windows are not supported by this installer. It installs under `~/.local/share/openbacktesting-studio/`, without `sudo` or changes to your system Python. Studio runs trusted local Python with your user permissions.

[View the installer source](../../../scripts/install-studio.sh). For manual builds, Python dependencies, and command-line options, see [local development](../development.md#studio-development) and the [Studio maintainer guide](../../../studio/docs/development.md).
