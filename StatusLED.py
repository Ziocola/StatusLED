import sys
import asyncio
import threading
import traceback

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QPlainTextEdit,
    QGroupBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QTimer
from bleak import BleakScanner, BleakClient

SERVICE_UUID = "2B29FEA3-1B1D-E522-D1A4-0A6083CC5C40"

class StatusLEDApp(QWidget):
    def __init__(self, loop):
        super().__init__()
        self.loop = loop
        self.client = None
        self.selected_char = None
        self._setup_ui()
        # Delay initial scan until UI is shown
        QTimer.singleShot(200, self.start_scan)

    def _setup_ui(self):
        # Window properties
        self.setWindowTitle("Status LED BLE Controller")
        self.setWindowIcon(QIcon.fromTheme("network-wireless"))
        self.resize(200, 350)

        # Dark theme stylesheet
        self.setStyleSheet(r"""
            QWidget { background: #282C34; color: #ABB2BF; font-size: 13px; }
            QLabel#title { color: #61AFEF; font-size: 20px; font-weight: bold; }
            QGroupBox { border: 1px solid #3E4451; border-radius: 4px; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 2px 8px; color: #98C379; font-weight: bold; }
            QComboBox { background: #21252B; border: 1px solid #3E4451; border-radius: 4px; padding: 4px; }
            QPushButton { border-radius: 4px; padding: 6px 12px; }
            QPushButton#scanBtn { background: #61AFEF; color: #282C34; }
            QPushButton#btn1 { background: #E06C75; color: #FFFFFF; }
            QPushButton#btn2 { background: #98C379; color: #FFFFFF; }
            QPushButton#btn3 { background: #b879c3; color: #FFFFFF; }
            QPlainTextEdit { background: #21252B; border: 1px solid #3E4451; border-radius: 4px; }
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Title
        lbl_title = QLabel("Status LED BLE Controller", objectName="title")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(lbl_title)

        # Status & Scan Row
        grp_status = QGroupBox()
        h_status = QHBoxLayout(grp_status)
        h_status.setContentsMargins(8, 4, 8, 4)
        self.lbl_status = QLabel("🔍 Pronto a scansionare")
        btn_scan = QPushButton("🔄", objectName="scanBtn")
        btn_scan.clicked.connect(self.start_scan)
        h_status.addWidget(self.lbl_status)
        h_status.addStretch()
        h_status.addWidget(btn_scan)
        layout.addWidget(grp_status)

        # Characteristic selector (collapsible)
        self.grp_char = QGroupBox("1) Seleziona caratteristica WRITE")
        self.grp_char.setCheckable(True)
        self.grp_char.setChecked(False)
        self.grp_char.toggled.connect(self.grp_char.setVisible)
        v_char = QVBoxLayout(self.grp_char)
        v_char.setContentsMargins(8, 8, 8, 8)
        self.cmb_chars = QComboBox()
        self.cmb_chars.setEnabled(False)
        self.cmb_chars.currentTextChanged.connect(lambda c: setattr(self, 'selected_char', c))
        v_char.addWidget(self.cmb_chars)
        self.grp_char.setVisible(False)
        layout.addWidget(self.grp_char)

        # Command buttons
        grp_cmd = QGroupBox("Comandi LED")
        h_cmd = QHBoxLayout(grp_cmd)
        h_cmd.setContentsMargins(8, 8, 8, 8)
        h_cmd.setSpacing(16)
        self.btn1 = QPushButton("🔴 Busy", objectName="btn1")
        self.btn2 = QPushButton("🟢 Free", objectName="btn2")
        self.btn3 = QPushButton("🟣 D.N.D.", objectName="btn3")
        for btn, code in ((self.btn1, '1'), (self.btn2, '2'), (self.btn3, '3')):
            btn.setEnabled(False)
            btn.clicked.connect(lambda _, c=code: self.enqueue_send(c))
            h_cmd.addWidget(btn)
        layout.addWidget(grp_cmd)

        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Log group (collapsible)
        self.grp_log = QGroupBox("Log")
        self.grp_log.setCheckable(True)
        self.grp_log.setChecked(False)
        self.grp_log.toggled.connect(self.grp_log.setVisible)
        v_log = QVBoxLayout(self.grp_log)
        v_log.setContentsMargins(8, 8, 8, 8)
        self.txt_log = QPlainTextEdit(objectName="log_view")
        self.txt_log.setReadOnly(True)
        v_log.addWidget(self.txt_log)
        self.grp_log.setVisible(False)
        layout.addWidget(self.grp_log)

    def log(self, message: str):
        self.txt_log.appendPlainText(message)

    def start_scan(self):
        self.log("--- Avvio scansione BLE ---")
        self.lbl_status.setText("🔍 Scansione BLE…")
        self.cmb_chars.clear(); self.cmb_chars.setEnabled(False)
        for btn in (self.btn1, self.btn2, self.btn3): btn.setEnabled(False)
        # Disconnect old client
        if self.client and getattr(self.client, 'is_connected', False):
            fut = asyncio.run_coroutine_threadsafe(self.client.disconnect(), self.loop)
            try: fut.result(2)
            except: pass
            self.client = None
        # Start new scan
        asyncio.run_coroutine_threadsafe(self._run_ble(), self.loop)

    async def _run_ble(self):
        try:
            self.log("⏳ Discovering BLE devices…")
            device = await BleakScanner.find_device_by_filter(
                lambda d, a: SERVICE_UUID.lower() in (u.lower() for u in (a.service_uuids or [])),
                timeout=5.0
            )
            if not device:
                raise RuntimeError("Device not found")
            self.log(f"✅ Trovato {device.address}")
            self.lbl_status.setText(f"🔗 Connessione a {device.address}…")

            client = BleakClient(device.address)
            await client.connect()
            if not client.is_connected:
                raise RuntimeError("Connessione fallita")
            self.client = client
            self.lbl_status.setText("✅ Connesso e pronto")

            self.log("📟 Recupero caratteristiche write…")
            # Populate write characteristics
            for svc in client.services:
                for char in svc.characteristics:
                    if 'write' in char.properties:
                        self.cmb_chars.addItem(char.uuid)
            if self.cmb_chars.count() == 0:
                raise RuntimeError("Nessuna char write")
            self.selected_char = self.cmb_chars.currentText()
            self.cmb_chars.setEnabled(True)
            for btn in (self.btn1, self.btn2, self.btn3): btn.setEnabled(True)
            self.log("✅ Pronto per comandi")

        except Exception as e:
            self.log(f"❌ Errore BLE: {e}")
            traceback.print_exc()
            self.lbl_status.setText("❌ Errore BLE")

    def enqueue_send(self, cmd: str):
        if not (self.client and self.client.is_connected and self.selected_char):
            self.log("⚠️ Non connesso o char non selezionata")
            return
        asyncio.run_coroutine_threadsafe(
            self.client.write_gatt_char(self.selected_char, cmd.encode(), response=True), self.loop
        )
        self.log(f"📤 Comando inviato: {cmd}")


def main():
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()
    app = QApplication(sys.argv)
    window = StatusLEDApp(loop)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
