import pytest
from pathlib import Path

from gltest.direct.sdk_loader import setup_sdk_paths


setup_sdk_paths(Path("contracts/visual_state_gate.py"))


def _patch_windows_fd0_unlink() -> None:
    import os
    import sys
    import tempfile

    if sys.platform != "win32":
        return

    import gltest.direct.loader as loader

    def tolerant_inject_message_to_fd0(vm):
        try:
            from genlayer.py import calldata
            from genlayer.py.types import Address
        except ImportError:
            return

        sender_addr = vm.sender
        if isinstance(sender_addr, bytes):
            sender_addr = Address(sender_addr)

        contract_addr = vm._contract_address
        if isinstance(contract_addr, bytes):
            contract_addr = Address(contract_addr)

        origin_addr = vm.origin
        if isinstance(origin_addr, bytes):
            origin_addr = Address(origin_addr)

        message_data = {
            "contract_address": contract_addr,
            "sender_address": sender_addr,
            "origin_address": origin_addr,
            "stack": [],
            "value": vm._value,
            "datetime": vm._datetime,
            "is_init": False,
            "chain_id": vm._chain_id,
            "entry_kind": 0,
            "entry_data": b"",
            "entry_stage_data": None,
        }

        encoded = calldata.encode(message_data)
        fd, path = tempfile.mkstemp()
        try:
            os.write(fd, encoded)
            os.lseek(fd, 0, os.SEEK_SET)
            original_stdin = os.dup(0)
            vm._original_stdin_fd = original_stdin
            os.dup2(fd, 0)
        finally:
            os.close(fd)
            try:
                os.unlink(path)
            except PermissionError:
                pass

    loader._inject_message_to_fd0 = tolerant_inject_message_to_fd0


_patch_windows_fd0_unlink()


def _patch_mocked_screenshot_bytes() -> None:
    import base64

    import gltest.direct.wasi_mock as wasi_mock
    from gltest.direct.wasi_mock import MockNotFoundError

    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
    )

    def handle_web_render(vm, data):
        url = data.get("url", "")
        mode = data.get("mode", "text")
        mock_data = vm._match_web_mock(url, "GET")
        if mock_data:
            body = mock_data.get("body", "")
            if "response" in mock_data:
                body = mock_data["response"].get("body", "")
            if isinstance(body, bytes):
                body = body.decode("utf-8", errors="replace")
            if mode == "screenshot":
                return {"ok": {"image": png}}
            return {"ok": {"text": body}}

        strict = getattr(vm, "_strict_mock_mode", False)
        if strict:
            registered = [f"GET {p.pattern}" for p, r in vm._web_mocks]
            raise MockNotFoundError(
                f"[strict] No web mock for WebRender {url}\n"
                f"  Registered: {registered or '(none)'}"
            )

        registered = [f"GET {p.pattern}" for p, r in vm._web_mocks]
        raise MockNotFoundError(
            f"No web mock for WebRender {url}\n"
            f"  Registered: {registered or '(none)'}"
        )

    wasi_mock._handle_web_render = handle_web_render


_patch_mocked_screenshot_bytes()


@pytest.fixture(autouse=True)
def reset_known_contract():
    yield
    try:
        import genlayer.gl as gl

        gl.genvm_contracts.__known_contract__ = None
    except Exception:
        pass


def deploy_gate(direct_deploy, **kwargs):
    args = [
        kwargs.get("max_requests", 1000),
        kwargs.get("max_attempts", 3),
        kwargs.get("max_url_chars", 320),
        kwargs.get("max_condition_chars", 600),
        kwargs.get("max_subject_chars", 160),
        kwargs.get("max_evidence_chars", 500),
    ]
    return direct_deploy("contracts/visual_state_gate.py", *args)


def as_hex_address(value) -> str:
    if hasattr(value, "as_hex"):
        return value.as_hex
    from genlayer.py.types import Address

    return Address(value).as_hex
