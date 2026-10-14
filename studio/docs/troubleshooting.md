# Troubleshooting

| Symptom / category | Meaning and action |
| --- | --- |
| `SessionDenied` | Reopen the newly printed launch URL. Its fragment token exchanges once; refreshes use the existing local Cookie. |
| `HostDenied`, `OriginDenied`, `CsrfDenied` | Use the exact loopback URL from the host; cross-origin writes and forwarded hosts are rejected. |
| `ProtocolMismatch` | Use assets distributed with this Studio version; stale clients cannot negotiate another protocol. |
| `InterpreterIncompatible` | Install compatible core and Studio plus strategy dependencies in the selected interpreter, then restart. No automatic installation occurs. |
| `FileConflict`, `SnapshotConflict` | Review disk versus draft. Reload discards the draft only through the explicit button. Keep draft establishes the latest disk as a merge base; edit and save again. |
| `FileNotFound` | An external process deleted the file. Copy the preserved draft yourself; Studio does not silently recreate it. |
| `PathDenied`, `UnsupportedEncoding`, `FileTooLarge` | Select an ordinary, workspace-contained UTF-8 file within the editor limit. Internal directories and symbolic links are excluded. |
| `DiscoveryFailed` | Inspect the exact source snapshot, missing dependency, syntax error or ambiguous `@backtest` entry. Discovery imports modules but does not run strategy lifecycle methods. |
| `WorkerTimeout` | Discovery exceeded 30 seconds. Remove blocking import-time work; the host remains available. Running a strategy has no invented time limit; use Cancel. |
| `SchemaOutdated`, `SchemaMismatch` | Rediscover and explicitly review parameter migration. Renames, type/option/range changes are not silently accepted. |
| Input title error | The core's validation category and title identify the field. Disabled values are still validated; a step is not a divisibility requirement. |
| Naive/duplicate/unordered CSV times | Supply the source timezone and correct the source data yourself. Studio does not sort, deduplicate or infer timestamp units. |
| `QueueFull` | Eight waiting runs are already queued. Wait or cancel a queued run. One worker executes at a time. |
| `cancelling` | Termination has been accepted but the worker has not yet been reclaimed. This is not a completed cancellation. |
| `host_restarted` | The previous host stopped before a terminal result. Inspect preserved diagnostics and explicitly submit again if wanted. |
| `ArtifactCorrupt`, `InvalidArtifact` | A required member, digest, schema, feature or archive boundary failed. The run is isolated; do not treat its report as verified. |
| `PlottingUnavailable`, `PlottingIncompatible` | The valid Portfolio can still be read. Import compatible plotting data if available. |
| `ChartDetailBudget`, `ChartEventBudget` | The chosen display range exceeds semantic-detail limits. Read a narrower raw range; execution facts remain intact. |
| `RerunUnavailable`, `EnvironmentChanged` | Source/data/request or compatible environment are missing. Imported code is not executed. Create a trusted workspace and explicitly configure a new run. |
| Missing logs | Default shared archives omit logs; forced termination may lose buffered output. An empty view is not evidence of complete logs. |

Source-location buttons open the immutable run snapshot, clearly identifying whether
its revision matches today's disk file. Old line numbers never navigate into an
unrelated current revision. Files are polled every two seconds for external changes;
a dirty buffer retains its draft and exposes the competing disk version.
