import pytest
from fastapi.testclient import TestClient

from openbacktesting_studio.cli import bind_socket
from openbacktesting_studio.host import create_app

ORIGIN = "http://127.0.0.1:41999"
TOKEN = "local-test-token-1234567890"


def session(app):
    client = TestClient(app, base_url=ORIGIN)
    response = client.post("/api/v1/session", json={"token": TOKEN}, headers={"origin": ORIGIN})
    assert response.status_code == 200
    assert "HttpOnly" in response.headers["set-cookie"]
    client.headers.update(
        {"origin": ORIGIN, "x-studio-csrf": response.json()["csrf"], "x-studio-protocol": "1"}
    )
    return client


def test_authentication_protocol_origin_and_single_use(tmp_path):
    app = create_app(tmp_path, origin=ORIGIN, token=TOKEN)
    client = TestClient(app, base_url=ORIGIN)
    assert client.get("/api/v1/files").status_code == 403
    with session(app) as client:
        assert client.get("/api/v1/capabilities").json()["mode"] == "workspace"
        assert client.post("/api/v1/session", json={"token": TOKEN}).status_code == 403
        assert client.get("/api/v1/files", headers={"host": "evil.test"}).status_code == 403
        assert client.get("/api/v1/files", headers={"x-studio-protocol": "2"}).status_code == 409
        assert (
            client.put("/api/v1/file", json={}, headers={"origin": "https://evil.test"}).status_code
            == 403
        )
        assert (
            client.put("/api/v1/file", json={}, headers={"x-studio-csrf": "wrong"}).status_code
            == 403
        )
        assert client.put("/api/v1/file", json={}).json()["fieldErrors"]


def test_file_api_saves_and_conflicts(tmp_path):
    path = tmp_path / "example.py"
    path.write_text("value = 1")
    with session(create_app(tmp_path, origin=ORIGIN, token=TOKEN)) as client:
        response = client.get("/api/v1/file", params={"path": "example.py"})
        assert response.status_code == 200
        assert "frame-ancestors" in response.headers["content-security-policy"]
        write = {
            "path": "example.py",
            "baseRevision": response.json()["revision"],
            "content": "value = 2",
        }
        assert client.put("/api/v1/file", json=write).status_code == 200
        assert path.read_text() == "value = 2"
        assert client.put("/api/v1/file", json=write).status_code == 409
        assert client.get("/api/v1/file", params={"path": "../outside"}).status_code in {403, 422}


def test_readonly_has_no_execution_routes(tmp_path):
    with session(create_app(None, origin=ORIGIN, readonly=True, token=TOKEN)) as client:
        assert client.get("/api/v1/capabilities").json()["mode"] == "view"
        for path in ["/file", "/discover", "/runs"]:
            assert client.post("/api/v1" + path, json={}).status_code in {404, 405}


def test_ephemeral_port_and_busy_port_are_non_destructive():
    with bind_socket() as first:
        port = first.getsockname()[1]
        with pytest.raises(OSError):
            bind_socket(port=port)
        assert first.getsockname()[1] == port
    with pytest.raises(ValueError):
        bind_socket("0.0.0.0")


def test_real_http_edit_discover_run_report_and_import(tmp_path):
    import json
    import time
    from pathlib import Path

    from test_runs import SOURCE

    (tmp_path / "strategy.py").write_text(SOURCE)
    with session(create_app(tmp_path, origin=ORIGIN, token=TOKEN)) as client:
        file = client.get("/api/v1/file", params={"path": "strategy.py"}).json()
        assert client.get("/api/v1/session").json()["csrf"]
        source = {"path": "strategy.py", "revision": file["revision"]}
        description = client.post("/api/v1/discover", json=source).json()["description"]
        payload = {
            "source": source,
            "inputs": {key: description[key] for key in ["schemaVersion", "schemaHash"]}
            | {"values": {}},
            "data": {
                "name": "GOOG",
                "kind": "sample",
                "sample": "GOOG",
                "timezone": "UTC",
                "timeframe": {"unit": "day", "multiplier": 1},
                "instrument": {"symbol": "GOOG"},
            },
            "idempotencyKey": "http-run",
        }
        response = client.post("/api/v1/runs", json=payload)
        assert response.status_code == 200, response.text
        run = response.json()
        for _ in range(200):
            run = client.get("/api/v1/runs/" + run["id"]).json()
            if run["status"] in {"succeeded", "failed"}:
                break
            time.sleep(0.02)
        assert run["status"] == "succeeded", run
        prefix = "/api/v1/runs/" + run["id"]
        for suffix in [
            "/summary",
            "/trades",
            "/curve",
            "/catalog",
            "/chart",
            "/provenance",
            "/logs",
        ]:
            assert client.get(prefix + suffix).status_code == 200, suffix
        assert client.get(prefix + "/workspace-match").json()["matches"] is True
        (tmp_path / "strategy.py").write_text("current_source = 2")
        assert client.get(prefix + "/workspace-match").json()["matches"] is False
        old_source = client.get(prefix + "/source?path=strategy.py").json()
        assert old_source["content"] == SOURCE and old_source["currentMatches"] is False
        bundle = client.get(prefix + "/export").content
        imported = client.post(
            "/api/v1/imports", content=bundle, headers={"content-type": "application/octet-stream"}
        )
        assert imported.status_code == 200
        assert client.get("/api/v1/runs/" + imported.json()["id"] + "/summary").status_code == 200
        assert (
            client.post(
                "/api/v1/imports",
                content=b"not a zip",
                headers={"content-type": "application/octet-stream"},
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/imports", content=b"{}", headers={"content-type": "application/json"}
            ).status_code
            == 422
        )
        fixture = (Path(__file__).parent / "fixtures/portfolio.json").read_bytes()
        imported = client.post(
            "/api/v1/imports", content=fixture, headers={"content-type": "application/json"}
        )
        assert imported.status_code == 200
        assert (
            client.get("/api/v1/runs/" + imported.json()["id"] + "/summary").json()["summary"]
            == json.loads(fixture)["summary"]
        )


def test_event_reset_response_is_scoped_to_host_instance(tmp_path):
    with session(create_app(tmp_path, origin=ORIGIN, token=TOKEN)) as client:
        response = client.get("/api/v1/events?instance=previous-instance&after=10")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert response.text.startswith("event: reset\n")
        assert '"expired": true' in response.text
        assert "local-test-token" not in response.text


def test_manual_workspace_selection_is_lazy_and_scoped(tmp_path, monkeypatch):
    from openbacktesting_studio.workspace import Workspace

    child = tmp_path / "strategies"
    child.mkdir()
    (child / "one.py").write_text("value = 1")
    (tmp_path / "outside.py").write_text("outside = True")
    scans = []
    original = Workspace.list
    monkeypatch.setattr(
        Workspace, "list", lambda self: (scans.append(self.root), original(self))[1]
    )
    app = create_app(tmp_path, origin=ORIGIN, token=TOKEN, choose_workspace=True)
    with session(app) as client:
        cap = client.get("/api/v1/capabilities").json()
        assert cap["workspace"] is None and not cap["capabilities"]["edit"]
        assert client.get("/api/v1/files").json()["code"] == "WorkspaceRequired"
        assert not (tmp_path / ".openbacktesting").exists()
        listing = client.get("/api/v1/directories").json()
        assert listing["directories"] == ["strategies"] and not scans
        chosen = client.put("/api/v1/workspace", json={"path": str(child)}).json()
        identity = chosen["workspaceId"]
        assert chosen["workspace"] == str(child)
        assert client.get("/api/v1/files").json()["files"] == ["one.py"]
        assert scans == [child]
        assert client.get("/api/v1/file?path=../outside.py").status_code == 403
        again = client.put("/api/v1/workspace", json={"path": str(child)}).json()
        assert again["workspaceId"] == identity
        assert (
            client.put("/api/v1/workspace", json={"path": str(child / "missing")}).status_code
            == 422
        )
        assert client.get("/api/v1/capabilities").json()["workspace"] == str(child)
        # A stale tab must not write a relative path into a newly selected directory.
        next_root = tmp_path / "other"
        next_root.mkdir()
        (next_root / "one.py").write_text("value = 2")
        assert client.put("/api/v1/workspace", json={"path": str(next_root)}).status_code == 200
        response = client.put("/api/v1/file", json={}, headers={"x-studio-workspace": identity})
        assert response.json()["code"] == "WorkspaceChanged"
        assert (next_root / "one.py").read_text() == "value = 2"
        assert client.get("/api/v1/files").json()["files"] == ["one.py"]


def test_workspace_switch_preserves_active_manager_and_readonly_boundary(tmp_path, monkeypatch):
    child = tmp_path / "child"
    child.mkdir()
    app = create_app(tmp_path, origin=ORIGIN, token=TOKEN)
    with session(app) as client:
        old = app.state.manager
        with monkeypatch.context() as scoped:
            scoped.setattr(old, "history", lambda: [{"status": "running"}])
            response = client.put("/api/v1/workspace", json={"path": str(child)})
        assert response.status_code == 409 and response.json()["code"] == "WorkspaceBusy"
        assert app.state.manager is old
        assert client.get("/api/v1/capabilities").json()["workspace"] == str(tmp_path)
    with session(create_app(None, origin=ORIGIN, readonly=True, token=TOKEN)) as client:
        assert client.put("/api/v1/workspace", json={"path": str(child)}).status_code in {404, 405}
        assert client.get("/api/v1/directories").status_code == 404


@pytest.mark.parametrize("kind", ["profiles", "presets"])
def test_configuration_http_roundtrip_uses_json_body(tmp_path, kind):
    from test_data import profile

    value = (
        profile().model_dump()
        if kind == "profiles"
        else {
            "schemaVersion": 1,
            "name": "QA preset",
            "inputs": {"schemaVersion": "1.0.0", "schemaHash": "qa", "values": {}},
            "settings": {"cash": 12000},
        }
    )
    with session(create_app(tmp_path, origin=ORIGIN, token=TOKEN)) as client:
        response = client.put(f"/api/v1/{kind}/qa", json=value)
        assert response.status_code == 200, response.text
        assert response.json() == value
        assert client.get(f"/api/v1/{kind}").json() == {"items": [{"id": "qa", "value": value}]}
        invalid = client.put(f"/api/v1/{kind}/qa", json=value | {"schemaVersion": 99})
        assert invalid.status_code == 422
        assert "schemaVersion" in invalid.json()["fieldErrors"]
        assert client.get(f"/api/v1/{kind}").json()["items"][0]["value"] == value


@pytest.mark.parametrize("payload", [None, [], 42, "text", {}])
def test_invalid_json_import_has_a_concise_error_and_no_history_entry(tmp_path, payload):
    import json

    with session(create_app(tmp_path, origin=ORIGIN, token=TOKEN)) as client:
        response = client.post(
            "/api/v1/imports",
            content=json.dumps(payload),
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 422, response.text
        message = response.json()["message"]
        assert 0 < len(message) < 1000
        assert "Failed validating" not in message
        assert client.get("/api/v1/runs").json() == {"runs": []}
