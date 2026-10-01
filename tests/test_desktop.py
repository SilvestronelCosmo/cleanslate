"""Desktop persistence checks without opening a window or listening on a port."""

import importlib.util
from pathlib import Path
import sys
from unittest.mock import Mock

import pytest


@pytest.fixture
def desktop(monkeypatch):
    monkeypatch.setitem(sys.modules, "webview", Mock())
    cocoa = Mock()
    cocoa.NSBundle.mainBundle.return_value.infoDictionary.return_value = {}
    cocoa.NSBundle.mainBundle.return_value.localizedInfoDictionary.return_value = None
    monkeypatch.setitem(sys.modules, "Foundation", cocoa)
    spec = importlib.util.spec_from_file_location("test_desktop_launcher", Path(__file__).parents[1] / "cleanslate/desktop.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    listener = Mock()
    monkeypatch.setattr(module.socket, "socket", Mock(return_value=listener))
    monkeypatch.setattr(module.threading, "Thread", Mock())
    monkeypatch.setattr(module, "is_port_in_use", Mock(return_value=True))
    monkeypatch.delenv("CLEANSLATE_PORT", raising=False)
    return module, listener


def test_desktop_keeps_origin_and_web_storage(desktop):
    module, listener = desktop
    for _ in range(2):
        with pytest.raises(SystemExit) as exit_info:
            module.main()
        assert exit_info.value.code == 0
    port = module.DEFAULT_PORT
    assert [call.args for call in listener.bind.call_args_list] == [(("127.0.0.1", port),)] * 2
    assert [call.kwargs["url"] for call in module.webview.create_window.call_args_list] == [f"http://127.0.0.1:{port}"] * 2
    assert all(call.kwargs["private_mode"] is False for call in module.webview.start.call_args_list)
    assert module.threading.Thread.call_args.kwargs["args"] == (port, listener)


def test_desktop_falls_back_to_the_next_port_when_the_default_is_busy(desktop, monkeypatch):
    module, listener = desktop
    monkeypatch.setattr(module, "alert", Mock())
    listener.bind.side_effect = [OSError("busy"), None]
    with pytest.raises(SystemExit):
        module.main()
    assert [call.args for call in listener.bind.call_args_list] == [(("127.0.0.1", module.DEFAULT_PORT),), (("127.0.0.1", module.DEFAULT_PORT + 1),)]
    assert module.webview.create_window.call_args.kwargs["url"] == f"http://127.0.0.1:{module.DEFAULT_PORT + 1}"


def test_desktop_does_not_open_another_service_on_busy_port(desktop, monkeypatch):
    module, listener = desktop
    monkeypatch.setattr(module, "alert", Mock())
    listener.bind.side_effect = OSError("busy")
    with pytest.raises(SystemExit, match="porta locale occupata"):
        module.main()
    module.webview.create_window.assert_not_called()
    module.threading.Thread.assert_not_called()
    assert listener.close.call_count == module.FALLBACK_PORTS
    module.alert.assert_called_once()
    monkeypatch.setenv("CLEANSLATE_PORT", "9999")
    listener.bind.reset_mock()
    with pytest.raises(SystemExit, match="porta locale occupata"):
        module.main()
    assert listener.bind.call_count == 1  # a port chosen by hand: no fallback


def test_desktop_passes_reserved_socket_to_server(desktop, monkeypatch):
    module, listener = desktop
    server = Mock()
    monkeypatch.setattr(module.uvicorn, "Server", Mock(return_value=server))
    module.run_uvicorn(module.DEFAULT_PORT, listener)
    server.run.assert_called_once_with(sockets=[listener])


def test_macos_name_is_set_before_server_and_window(desktop, monkeypatch):
    module, _ = desktop
    monkeypatch.setattr(module.sys, "platform", "darwin")
    cocoa = sys.modules["Foundation"]
    info, localized = {}, {}
    cocoa.NSBundle.mainBundle.return_value.infoDictionary.return_value = info
    cocoa.NSBundle.mainBundle.return_value.localizedInfoDictionary.return_value = localized

    def check_name(**kwargs):
        cocoa.NSProcessInfo.processInfo.return_value.setProcessName_.assert_called_once_with("CleanSlate")
        assert info["CFBundleName"] == localized["CFBundleDisplayName"] == "CleanSlate"
        return Mock()

    module.threading.Thread.side_effect = check_name
    with pytest.raises(SystemExit):
        module.main()


def test_macos_name_is_skipped_on_other_platforms(desktop, monkeypatch):
    module, _ = desktop
    monkeypatch.setattr(module.sys, "platform", "linux")
    module.configure_macos_name()
    sys.modules["Foundation"].NSBundle.mainBundle.assert_not_called()


@pytest.mark.parametrize("value", ["abc", "0", "65536", "-1"])
def test_desktop_rejects_invalid_port(desktop, monkeypatch, value):
    module, listener = desktop
    monkeypatch.setenv("CLEANSLATE_PORT", value)
    with pytest.raises(SystemExit, match="tra 1 e 65535"):
        module.reserve_port()
    listener.bind.assert_not_called()
