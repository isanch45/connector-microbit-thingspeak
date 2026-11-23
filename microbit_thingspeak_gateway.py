# SPDX-License-Identifier: EUPL-1.2
# © 2026 Generalitat de Catalunya · Departament d'Educació i Formació Professional
#
# Reconstrucció funcional del codi de Connector Microbit-ThingSpeak-Serial v5.1.4.
# Basada en el bytecode CPython 3.12 extret de l'EXE original (SHA-256 documentat
# al README). No és el fitxer .py original, que no s'ha pogut recuperar literalment.
# L'actiu gràfic institucional de l'EXE no s'inclou en aquest repositori.
"""Pont USB/sèrie entre una BBC micro:bit i els camps d'un canal ThingSpeak."""

from __future__ import annotations

import ctypes
import json
import os
import sys
import threading
import time
import webbrowser
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import requests
import serial
from serial.tools import list_ports

APP_NAME = "Connector Microbit-ThingSpeak-Serial v5.1.5 (prova)"
APP_VERSION = "5.1.5-prova"
PROJECT_NAME = "Estació Meteorològica en Xarxa"
AUTHOR = "Ignasi Sánchez Rodríguez"
PROGRAM_NAME = "Mentoria 4.0"
COPYRIGHT_NOTICE = (
    "© 2026 Generalitat de Catalunya · Departament d’Educació "
    "i Formació Professional"
)
LICENSE_NAME = "EUPL 1.2"
LICENSE_URL = (
    "https://interoperable-europe.ec.europa.eu/sites/default/files/"
    "inline-files/EUPL%20v1_2%20ES.txt"
)
LEGACY_CONFIG_FILE = "microbit_thingspeak_config.json"
PORTABLE_CONFIG_FILE = "microbit_thingspeak_portable.json"
APP_CONFIG_FOLDER = "Microbit-ThingSpeak-Gateway"
BAUD = 115200
DEFAULT_INTERVAL = 15

# Keep the OS awake but leave display power management untouched.
# These flags are per-thread and must be cleared from the SAME thread.
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001


class WindowsSleepGuard:
    """Prevent idle sleep while the micro:bit USB worker is active."""

    def __init__(self) -> None:
        self.active = False
        self._set_execution_state = None

    def enable(self) -> bool:
        if sys.platform != "win32":
            return False
        try:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            fn = kernel32.SetThreadExecutionState
            fn.argtypes = [ctypes.c_uint]
            fn.restype = ctypes.c_uint
            if not fn(ES_CONTINUOUS | ES_SYSTEM_REQUIRED):
                return False
        except (OSError, AttributeError, TypeError):
            return False
        self._set_execution_state = fn
        self.active = True
        return True

    def release(self) -> None:
        if self._set_execution_state is not None:
            try:
                self._set_execution_state(ES_CONTINUOUS)
            except (OSError, AttributeError, TypeError):
                pass
            finally:
                self._set_execution_state = None
                self.active = False


def app_dir() -> str:
    """Directori de l'executable o del fitxer Python en desenvolupament."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def appdata_dir() -> str:
    """Carpeta personal on es desa la configuració, fora de Program Files."""
    base = os.environ.get("APPDATA") or os.path.join(
        os.path.expanduser("~"), ".config"
    )
    return os.path.join(base, APP_CONFIG_FOLDER)


USER_CONFIG_PATH = os.path.join(appdata_dir(), "config.json")
LEGACY_CONFIG_PATH = os.path.join(app_dir(), LEGACY_CONFIG_FILE)
PORTABLE_CONFIG_PATH = os.path.join(app_dir(), PORTABLE_CONFIG_FILE)


def read_config_file(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        return None
    return None


def load_config() -> dict:
    """Prioritat: configuració portable, AppData, format antic."""
    cfg = {"api_key": "", "interval": DEFAULT_INTERVAL}
    for path in (PORTABLE_CONFIG_PATH, USER_CONFIG_PATH, LEGACY_CONFIG_PATH):
        data = read_config_file(path)
        if data is None:
            continue
        cfg.update(data)
        if path == LEGACY_CONFIG_PATH and cfg.get("api_key"):
            try:
                save_config(cfg)
            except OSError:
                pass
        return cfg
    return cfg


def save_config(cfg: dict) -> None:
    """Desament atòmic; el mode portable només s'activa si existeix el fitxer."""
    path = (
        PORTABLE_CONFIG_PATH
        if os.path.isfile(PORTABLE_CONFIG_PATH)
        else USER_CONFIG_PATH
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = path + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def find_microbit_port() -> str | None:
    """Busca el port sèrie de la micro:bit, o l'únic port si només n'hi ha un."""
    ports = list(list_ports.comports())
    keywords = ("micro:bit", "microbit", "cmsis-dap", "mbed")
    for port in ports:
        text = " ".join(
            str(value or "")
            for value in (
                port.description,
                port.manufacturer,
                port.product,
                port.hwid,
            )
        ).lower()
        if any(key in text for key in keywords):
            return port.device
    if len(ports) == 1:
        return ports[0].device
    return None


class GatewayApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title(APP_NAME)
        root.geometry("650x350")
        root.resizable(False, False)

        self.cfg = load_config()
        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.ser: serial.Serial | None = None
        self.last_raw_response = ""
        self.last_sent_line = ""
        self.last_entry_id = ""
        self.sleep_guard_active = False

        frame = ttk.Frame(root, padding=18)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame, text="Micro:bit → ThingSpeak", font=("Segoe UI", 17, "bold")
        ).pack(anchor="w")
        ttk.Label(
            frame,
            text="Pont automàtic USB/Serial → Internet → ThingSpeak",
        ).pack(anchor="w", pady=(2, 16))

        box = ttk.LabelFrame(frame, text="Estat", padding=12)
        box.pack(fill="x")

        self.status_var = tk.StringVar(value="Iniciant...")
        ttk.Label(
            box, textvariable=self.status_var, font=("Segoe UI", 12, "bold")
        ).pack(anchor="w")
        self.detail_var = tk.StringVar(value="Preparant...")
        ttk.Label(
            box, textvariable=self.detail_var, wraplength=500
        ).pack(anchor="w", pady=(8, 0))

        ttk.Separator(frame).pack(fill="x", pady=14)
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x")
        ttk.Button(
            buttons, text="Reinicia pont", command=self.restart_gateway
        ).pack(side="left")
        ttk.Button(
            buttons, text="Canvia API Key", command=self.change_api_key
        ).pack(side="left", padx=8)
        ttk.Button(buttons, text="Debug", command=self.show_debug).pack(
            side="left"
        )
        ttk.Button(buttons, text="ℹ Quant a", command=self.show_about).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(buttons, text="Surt", command=self.on_close).pack(
            side="right"
        )
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        if not self.cfg.get("api_key"):
            root.after(250, self.first_run_setup)
        else:
            root.after(400, self.start_gateway)

    def first_run_setup(self) -> None:
        key = simpledialog.askstring(
            APP_NAME,
            "Primera configuració.\n\n"
            "Enganxa la Write API Key del teu canal de ThingSpeak:",
            parent=self.root,
        )
        if not key:
            self.ui(
                "Falta configurar ThingSpeak",
                "Prem 'Canvia API Key' per configurar-lo.",
            )
            return

        self.cfg["api_key"] = key.strip()
        self.cfg["interval"] = max(
            DEFAULT_INTERVAL, int(self.cfg.get("interval", DEFAULT_INTERVAL))
        )
        save_config(self.cfg)
        self.ui("Configuració guardada", "Buscant la micro:bit...")
        self.root.after(300, self.start_gateway)

    def change_api_key(self) -> None:
        key = simpledialog.askstring(
            APP_NAME,
            "Nova Write API Key de ThingSpeak:",
            initialvalue=self.cfg.get("api_key", ""),
            parent=self.root,
        )
        if key:
            self.cfg["api_key"] = key.strip()
            save_config(self.cfg)
            messagebox.showinfo(APP_NAME, "API Key guardada.")
            self.restart_gateway()

    def show_about(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Quant a")
        win.geometry("650x425")
        win.resizable(False, False)
        frm = ttk.Frame(win, padding=18)
        frm.pack(fill="both", expand=True)
        top = ttk.Frame(frm)
        top.pack(fill="x")

        # L'EXE incorporava un logotip institucional com a dades PNG.
        # Aquest fitxer reconstruït utilitza la icona original del projecte.
        resource_root = getattr(sys, "_MEIPASS", app_dir())
        icon_path = os.path.join(resource_root, "assets", "app_icon.png")
        if os.path.isfile(icon_path):
            try:
                img = tk.PhotoImage(file=icon_path)
                img = img.subsample(4, 4)
                label = ttk.Label(top, image=img)
                label.image = img
                label.pack(side="left", padx=(0, 15))
            except tk.TclError:
                pass

        ttk.Label(
            top,
            text="Connector Microbit-ThingSpeak-Serial",
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w")
        info = ttk.Frame(frm)
        info.pack(fill="both", expand=True, pady=(20, 0))
        for text in (
            f"Projecte: {PROJECT_NAME}",
            f"Desenvolupador del connector: {AUTHOR}",
            f"Programa: {PROGRAM_NAME}",
            f"Copyright: {COPYRIGHT_NOTICE}",
            f"Llicència del programari: {LICENSE_NAME}",
            "Materials educatius: CC BY-NC-SA 4.0",
            f"Versió: {APP_VERSION}",
        ):
            ttk.Label(info, text=text, wraplength=600).pack(anchor="w", pady=3)

        actions = ttk.Frame(frm)
        actions.pack(fill="x", side="bottom")
        ttk.Button(
            actions,
            text="Obre la llicència",
            command=lambda: webbrowser.open(LICENSE_URL),
        ).pack(side="left")
        ttk.Button(actions, text="Tanca", command=win.destroy).pack(
            side="right"
        )

    def show_debug(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Debug")
        win.geometry("700x420")
        frm = ttk.Frame(win, padding=18)
        frm.pack(fill="both", expand=True)
        ttk.Label(
            frm, text="Informació tècnica per a diagnosi i demostracions."
        ).pack(anchor="w", pady=(0, 12))
        info = tk.Text(frm, wrap="word")
        info.pack(fill="both", expand=True)
        port_text = (
            getattr(self.ser, "port", "No connectat")
            if self.ser and self.ser.is_open
            else "No connectat"
        )
        technical_text = (
            f"Port sèrie: {port_text}\n"
            f"Baud rate: {BAUD}\n"
            f"Repòs automàtic impedit: {'Sí (pantalla lliure)' if self.sleep_guard_active else 'No'}\n"
            f"Interval mínim: {self.cfg.get('interval', DEFAULT_INTERVAL)} s"
            "\n\nÚltima línia rebuda:\n"
            f"{self.last_sent_line or '(cap)'}"
            "\n\nÚltim entry_id:\n"
            f"{self.last_entry_id or '(cap)'}"
            "\n\nResposta completa de ThingSpeak (JSON):\n"
            f"{self.last_raw_response or '(encara no hi ha resposta)'}"
        )
        info.insert("1.0", technical_text)
        info.configure(state="disabled")
        ttk.Button(frm, text="Tanca", command=win.destroy).pack(
            anchor="e", pady=(12, 0)
        )

    def ui(self, status: str | None = None, detail: str | None = None) -> None:
        def apply() -> None:
            if status is not None:
                self.status_var.set(status)
            if detail is not None:
                self.detail_var.set(detail)

        self.root.after(0, apply)

    def restart_gateway(self) -> None:
        self.stop_gateway()
        self.root.after(500, self.start_gateway)

    def start_gateway(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        if not self.cfg.get("api_key"):
            self.first_run_setup()
            return
        self.stop_event.clear()
        self.worker = threading.Thread(target=self.run_gateway, daemon=True)
        self.worker.start()

    def stop_gateway(self) -> None:
        self.stop_event.set()
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass

    def run_gateway(self) -> None:
        self.ui("Buscant micro:bit...", "Connecta la micro:bit per USB.")
        port = find_microbit_port()
        if not port:
            self.ui(
                "No s'ha trobat cap micro:bit",
                "Connecta-la per USB i prem 'Reinicia pont'.",
            )
            return
        try:
            self.ser = serial.Serial(port, BAUD, timeout=1)
            time.sleep(1.5)
        except Exception as exc:
            self.ui("Error obrint la micro:bit", str(exc))
            return

        sleep_guard = WindowsSleepGuard()
        self.sleep_guard_active = sleep_guard.enable()
        if self.sleep_guard_active:
            energy_note = "Repòs automàtic impedit; la pantalla es pot apagar."
        else:
            energy_note = "No s'ha pogut impedir el repòs; revisa l'energia de Windows."
        self.ui("✅ Connectat", f"Micro:bit detectada a {port}. {energy_note}")
        try:
            last_send = 0.0
            interval = max(
                DEFAULT_INTERVAL, int(self.cfg.get("interval", DEFAULT_INTERVAL))
            )
            while not self.stop_event.is_set():
                try:
                    raw = self.ser.readline()
                    if not raw:
                        continue
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue
                    parts = [x.strip() for x in line.split(",")]
                    if time.time() - last_send < interval:
                        continue

                    start = 0
                    if parts and not self.is_number(parts[0]):
                        start = 1
                    values = parts[start : start + 8]
                    if not values:
                        continue

                    payload = {"api_key": self.cfg["api_key"]}
                    for i, value in enumerate(values, start=1):
                        payload[f"field{i}"] = value

                    response = requests.post(
                        "https://api.thingspeak.com/update.json",
                        data=payload,
                        timeout=10,
                    )
                    response_text = response.text.strip()
                    self.last_raw_response = response_text
                    self.last_sent_line = line

                    if response.ok and response_text not in ("", "0"):
                        last_send = time.time()
                        try:
                            entry_id = str(response.json().get("entry_id", ""))
                        except Exception:
                            entry_id = response_text
                        self.last_entry_id = entry_id
                        shown = ", ".join(values)
                        detail = f"Últim valor enviat: {shown}"
                        if entry_id:
                            detail += f" · Entrada {entry_id}"
                        self.ui("✅ Enviant a ThingSpeak", detail)
                    else:
                        self.ui(
                            "ThingSpeak ha rebutjat l'enviament",
                            "Revisa la connexió o la Write API Key.",
                        )
                except serial.SerialException:
                    self.ui(
                        "Micro:bit desconnectada",
                        "Torna-la a connectar i prem 'Reinicia pont'.",
                    )
                    break
                except requests.RequestException:
                    self.ui(
                        "Sense connexió amb ThingSpeak",
                        "Comprova la connexió a Internet.",
                    )
                    time.sleep(2)
                except Exception as exc:
                    self.ui("Error", str(exc))
                    time.sleep(2)

        finally:
            # Clear the request on the worker thread that created it.
            sleep_guard.release()
            self.sleep_guard_active = False
            try:
                if self.ser and self.ser.is_open:
                    self.ser.close()
            except Exception:
                pass

    @staticmethod
    def is_number(text: str) -> bool:
        try:
            float(text)
            return True
        except Exception:
            return False

    def on_close(self) -> None:
        self.stop_gateway()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    GatewayApp(root)
    root.mainloop()
