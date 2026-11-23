"""Tests unitaris sense micro:bit ni Internet: verificació de la reconstrucció."""
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import microbit_thingspeak_gateway as gateway


class SleepGuardTests(unittest.TestCase):
    def test_system_stays_awake_without_forcing_display_on(self):
        fn = MagicMock(return_value=1)
        kernel32 = SimpleNamespace(SetThreadExecutionState=fn)
        with (
            patch.object(gateway.sys, "platform", "win32"),
            patch.object(gateway.ctypes, "WinDLL", return_value=kernel32, create=True),
        ):
            guard = gateway.WindowsSleepGuard()
            self.assertTrue(guard.enable())
            self.assertTrue(guard.active)
            guard.release()
            self.assertFalse(guard.active)
        self.assertEqual([c.args[0] for c in fn.call_args_list], [
            gateway.ES_CONTINUOUS | gateway.ES_SYSTEM_REQUIRED,
            gateway.ES_CONTINUOUS,
        ])
        self.assertFalse(fn.call_args_list[0].args[0] & 0x2)

    def test_non_windows_is_noop(self):
        with patch.object(gateway.sys, "platform", "linux"):
            guard = gateway.WindowsSleepGuard()
            self.assertFalse(guard.enable())
            guard.release()

    def test_api_failure_leaves_sleep_unchanged(self):
        fn = MagicMock(return_value=0)
        kernel32 = SimpleNamespace(SetThreadExecutionState=fn)
        with (
            patch.object(gateway.sys, "platform", "win32"),
            patch.object(gateway.ctypes, "WinDLL", return_value=kernel32, create=True),
        ):
            guard = gateway.WindowsSleepGuard()
            self.assertFalse(guard.enable())
            guard.release()
        fn.assert_called_once_with(gateway.ES_CONTINUOUS | gateway.ES_SYSTEM_REQUIRED)


class GatewayTests(unittest.TestCase):
    def test_detect_microbit_port(self):
        ports = [
            SimpleNamespace(
                description="USB Serial Device",
                manufacturer="Generic",
                product="Generic Serial",
                hwid="USB\\VID_ABCD",
                device="COM2",
            ),
            SimpleNamespace(
                description="BBC micro:bit",
                manufacturer="Micro:bit Foundation",
                product="CMSIS-DAP",
                hwid="USB\\VID_0D28",
                device="COM7",
            ),
        ]
        with patch.object(gateway.list_ports, "comports", return_value=ports):
            self.assertEqual(gateway.find_microbit_port(), "COM7")

    def test_single_port_fallback(self):
        p = SimpleNamespace(
            description="Another device",
            manufacturer="?",
            product="?",
            hwid="?",
            device="COM5",
        )
        with patch.object(gateway.list_ports, "comports", return_value=[p]):
            self.assertEqual(gateway.find_microbit_port(), "COM5")

    def test_no_serial_devices(self):
        with patch.object(gateway.list_ports, "comports", return_value=[]):
            self.assertIsNone(gateway.find_microbit_port())

    def test_config_store_and_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            user_path = str(folder / "saved" / "config.json")
            portable = str(folder / "portable.json")
            legacy = str(folder / "old.json")
            with (
                patch.object(gateway, "USER_CONFIG_PATH", user_path),
                patch.object(gateway, "PORTABLE_CONFIG_PATH", portable),
                patch.object(gateway, "LEGACY_CONFIG_PATH", legacy),
            ):
                gateway.save_config({"api_key": "EXAMPLE-NOT-REAL", "interval": 15})
                self.assertTrue(Path(user_path).is_file())
                self.assertEqual(
                    gateway.load_config()["api_key"], "EXAMPLE-NOT-REAL"
                )

    def test_config_legacy_migrates(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            user_path = str(folder / "user" / "config.json")
            portable = str(folder / "portable.json")
            legacy = str(folder / "legacy.json")
            Path(legacy).write_text(
                json.dumps({"api_key": "EXAMPLE", "interval": 20}),
                encoding="utf-8",
            )
            with (
                patch.object(gateway, "USER_CONFIG_PATH", user_path),
                patch.object(gateway, "PORTABLE_CONFIG_PATH", portable),
                patch.object(gateway, "LEGACY_CONFIG_PATH", legacy),
            ):
                self.assertEqual(gateway.load_config()["interval"], 20)
                self.assertTrue(Path(user_path).exists())

    def test_numeric_first_field(self):
        self.assertTrue(gateway.GatewayApp.is_number("23"))
        self.assertTrue(gateway.GatewayApp.is_number("-5.2"))
        self.assertFalse(gateway.GatewayApp.is_number("HORT"))

    def test_send_fields_to_thingspeak(self):
        app = gateway.GatewayApp.__new__(gateway.GatewayApp)
        app.stop_event = threading.Event()
        app.cfg = {"api_key": "EXAMPLE-NOT-REAL", "interval": 15}
        app.last_raw_response = ""
        app.last_sent_line = ""
        app.last_entry_id = ""
        statuses = []
        app.ui = lambda *args: statuses.append(args)

        fake_serial = MagicMock()
        fake_serial.is_open = True

        def first_readline():
            app.stop_event.set()
            return b"HORT,23,157,623\r\n"

        fake_serial.readline.side_effect = first_readline
        response = MagicMock()
        response.text = '{"entry_id": 42}'
        response.ok = True
        response.json.return_value = {"entry_id": 42}

        with (
            patch.object(gateway, "find_microbit_port", return_value="COM7"),
            patch.object(gateway.serial, "Serial", return_value=fake_serial),
            patch.object(gateway.requests, "post", return_value=response) as post,
            patch.object(gateway.time, "sleep"),
            patch.object(gateway.time, "time", return_value=100.0),
            patch.object(gateway, "WindowsSleepGuard") as sleep_guard,
        ):
            sleep_guard.return_value.enable.return_value = True
            app.run_gateway()
            sleep_guard.return_value.enable.assert_called_once()
            sleep_guard.return_value.release.assert_called_once()
            self.assertFalse(app.sleep_guard_active)

        post.assert_called_once()
        _, kwargs = post.call_args
        self.assertEqual(kwargs["data"]["api_key"], "EXAMPLE-NOT-REAL")
        self.assertEqual(kwargs["data"]["field1"], "23")
        self.assertEqual(kwargs["data"]["field2"], "157")
        self.assertEqual(kwargs["data"]["field3"], "623")
        self.assertEqual(app.last_entry_id, "42")
        self.assertTrue(any("Enviant" in status[0] for status in statuses))
        self.assertTrue(fake_serial.close.called)


if __name__ == "__main__":
    unittest.main()
