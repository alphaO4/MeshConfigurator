
> **Not affiliated with Meshtastic.** This project is an independent, community-built tool **for Meshtastic** devices and is not endorsed by Meshtastic LLC.


# Optional Installer (Windows)

Prefer not to build from source? An **EV-code-signed** Windows installer is available on Gumroad.
This is **purely optional** — the installer and the source build are functionally identical.

**[Get the Windows installer on Gumroad](your-gumroad-link)**

---

# Mesh Configurator

A focused, fast, and pragmatic GUI for configuring Meshtastic devices.
Built with `customtkinter`, it supports reading the device model, editing settings
(including modules), diffing, and applying changes via the Meshtastic CLI/API.

> **Note**
> Meshtastic® is a registered trademark of Meshtastic LLC. This project is not
> affiliated with or endorsed by Meshtastic LLC. See [TRADEMARKS](./TRADEMARKS.md).

---

## Features

* One-click **Detect/Connect** to a single device
* Panels for **Device**, **LoRa**, **Channels**, **Power**, **Position**, **Display**, **Bluetooth**, **Network**, and **Modules**
* **Diff-based apply** using the Meshtastic CLI (minimal writes; safe retries)
* **Presets**: save/apply groups of settings, including additional mesh channels
* **Disconnect & clear UI** to batch-configure multiple devices quickly
* Defensive error handling, redaction for sensitive values, readable logs

---

## Preset Storage & PSK Security

* **Automatic keychain use (when available).** If the system keychain is available via Python’s `keyring`, channel PSKs saved in presets are stored securely in the OS keychain. The preset file stores a **reference token**, not the secret. When loading/applying a preset, the app resolves tokens from the keychain automatically.
* **Graceful fallback.** If `keyring` isn’t available (or the keychain can’t be used), PSKs are stored **in plaintext** in the preset JSON. This keeps presets portable, but you should treat them as sensitive.
* **No surprise changes to behavior.** Aside from where the PSK value is persisted, functionality is identical. Logs and CLI calls continue to redact PSKs.
* **Portability.** Preset files that reference keychain entries can be shared, but the **PSKs will not travel** with the file. On another machine, you’ll need to set those PSKs before.
---

## Quick Start (from source)

```bash
# 1) Create and activate venv
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

# 2) Install
pip install -r requirements.txt
# (Optional, for secure presets)
pip install keyring

# 3) Run
python app.py
```

---

**Trademark Notice.** Meshtastic® is a registered trademark of Meshtastic LLC. Meshtastic software components are released under various licenses, see GitHub for details. No warranty is provided — use at your own risk.
