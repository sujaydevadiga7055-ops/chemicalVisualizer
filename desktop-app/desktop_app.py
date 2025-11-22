# desktop_app.py
"""
Professional Desktop UI for Chemical Equipment Visualizer (Version A base + improvements)

Features:
- KPI cards with bold values, larger fonts, subtle shadow, hover scale animation
- Large donut (donut) chart with centered total and right-side legend
- Bigger, clearer bar chart with dynamic y-axis scaling and value annotations
- Larger "Choose CSV" and "Upload" controls
- Bigger Upload History text and clickable list
- Background threads for network calls to keep UI responsive
- Export PDF button (calls API_REPORT endpoint)
- Clean modern palette and spacing to mimic the "second image" UI feel

Run:
  python desktop_app.py

Dependencies:
  pip install PyQt5 matplotlib requests
"""

import sys
import os
import threading
import requests
import webbrowser
from datetime import datetime

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# ---------------- CONFIG ----------------
API_UPLOAD = "http://127.0.0.1:8000/api/upload/"
API_LATEST = "http://127.0.0.1:8000/api/summary/latest/"
API_HISTORY = "http://127.0.0.1:8000/api/history/"
API_REPORT = "http://127.0.0.1:8000/api/report/{id}/"   # GET expected to return PDF bytes
TOKEN = "dc7115f7e1ded18dbebf810fb9788043f38a39b5"
HEADERS = {"Authorization": f"Token {TOKEN}"}
# ----------------------------------------

# Professional color palette
PALETTE = ["#2b8cbe", "#66c2a5", "#fdae61", "#d53e4f", "#9e9ac8", "#fc8d62"]

# ---------- Small utilities ----------
def threaded(fn):
    """Decorator to run function in a daemon thread."""
    def wrapper(*a, **kw):
        t = threading.Thread(target=fn, args=a, kwargs=kw, daemon=True)
        t.start()
        return t
    return wrapper

# ---------- Matplotlib canvas ----------
class ChartCanvas(FigureCanvas):
    def __init__(self, width=6, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        fig.patch.set_facecolor("none")

# ---------- Hover card with subtle scale animation ----------
class HoverCard(QtWidgets.QFrame):
    """Card with subtle enlarge animation on hover + drop shadow."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.anim = QtCore.QPropertyAnimation(self, b"geometry", self)
        self.anim.setDuration(140)
        self.anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        # shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(14)
        shadow.setColor(QtGui.QColor(0, 0, 0, 30))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)
        self._base_rect = None

    def enterEvent(self, ev):
        if self._base_rect is None:
            self._base_rect = self.geometry()
        r = self._base_rect
        enlarged = r.adjusted(-6, -6, 6, 6)
        self.anim.stop()
        self.anim.setStartValue(self.geometry())
        self.anim.setEndValue(enlarged)
        self.anim.start()
        super().enterEvent(ev)

    def leaveEvent(self, ev):
        if self._base_rect is None:
            return
        self.anim.stop()
        self.anim.setStartValue(self.geometry())
        self.anim.setEndValue(self._base_rect)
        self.anim.start()
        super().leaveEvent(ev)

# ---------- Main App ----------
class DesktopApp(QtWidgets.QWidget):
    # custom signals to update UI from worker threads
    sig_summary = pyqtSignal(object)
    sig_history = pyqtSignal(list)
    sig_status = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chemical Equipment Visualizer - Desktop")
        self.setMinimumSize(1150, 760)
        self.setWindowIcon(QtGui.QIcon())  # add path to icon if available
        QtWidgets.QApplication.setStyle("Fusion")

        # connect signals
        self.sig_summary.connect(self._on_summary)
        self.sig_history.connect(self._on_history)
        self.sig_status.connect(self._on_status)

        # file state
        self.file_path = None
        self.latest_dataset_id = None

        # build UI
        self._build_ui()

        # initial data load (small delay so UI shows fast)
        QtCore.QTimer.singleShot(250, self.fetch_all)

    def _build_ui(self):
        # root layout
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        # header
        h_layout = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Chemical Equipment Visualizer")
        title.setObjectName("mainTitle")
        title.setStyleSheet("font-family:Segoe UI; font-size:22px; font-weight:700; color:#0b3a53;")
        h_layout.addWidget(title)
        h_layout.addStretch()
        self.status_label = QtWidgets.QLabel("Desktop Dashboard")
        self.status_label.setStyleSheet("color:#666;")
        h_layout.addWidget(self.status_label)
        root.addLayout(h_layout)

        # Upload controls (prominent)
        upload_row = QtWidgets.QHBoxLayout()
        upload_row.setSpacing(12)
        self.btn_choose = QtWidgets.QPushButton("Choose CSV")
        self.btn_choose.setObjectName("chooseBtn")
        self.btn_choose.clicked.connect(self.choose_file)
        self.lbl_file = QtWidgets.QLabel("No file selected")
        self.lbl_file.setStyleSheet("color:#666; font-size:13px;")
        self.btn_upload = QtWidgets.QPushButton("Upload")
        self.btn_upload.setObjectName("primaryBtn")
        self.btn_upload.clicked.connect(self.upload_file)

        # put them
        upload_row.addWidget(self.btn_choose, 0)
        upload_row.addWidget(self.lbl_file, 1)
        upload_row.addStretch(1)
        upload_row.addWidget(self.btn_upload, 0)
        root.addLayout(upload_row)

        # KPI strip
        kpi_layout = QtWidgets.QHBoxLayout()
        kpi_layout.setSpacing(14)
        root.addLayout(kpi_layout)

        # build 4 KPI cards using HoverCard
        self.card_total = self._make_kpi_card("Total Count", "—")
        self.card_flow = self._make_kpi_card("Avg Flowrate", "—")
        self.card_pressure = self._make_kpi_card("Avg Pressure", "—")
        self.card_temp = self._make_kpi_card("Avg Temperature", "—")

        kpi_layout.addWidget(self.card_total)
        kpi_layout.addWidget(self.card_flow)
        kpi_layout.addWidget(self.card_pressure)
        kpi_layout.addWidget(self.card_temp)

        # main content split left / right
        content = QtWidgets.QHBoxLayout()
        content.setSpacing(16)
        root.addLayout(content)

        # LEFT: Summary + History + actions
        left = QtWidgets.QVBoxLayout()
        left.setSpacing(12)
        content.addLayout(left, 36)

        # Summary header & rich text
        lbl_summary = QtWidgets.QLabel("Latest Summary")
        lbl_summary.setStyleSheet("font-size:16px; font-weight:700;")
        left.addWidget(lbl_summary)

        self.summary_card = QtWidgets.QFrame()
        self.summary_card.setStyleSheet("background:white; border-radius:10px; padding:12px;")
        sc_layout = QtWidgets.QVBoxLayout(self.summary_card)
        sc_layout.setContentsMargins(10, 10, 10, 10)
        self.summary_text = QtWidgets.QLabel("No data loaded.")
        self.summary_text.setWordWrap(True)
        self.summary_text.setStyleSheet("font-size:13px; color:#333;")
        sc_layout.addWidget(self.summary_text)
        left.addWidget(self.summary_card)

        # Upload History
        hist_label = QtWidgets.QLabel("Upload History (Last 5):")
        hist_label.setStyleSheet("font-size:14px; font-weight:600;")
        left.addWidget(hist_label)

        self.history_list = QtWidgets.QListWidget()
        self.history_list.setStyleSheet("background:white; border-radius:8px; padding:6px;")
        self.history_list.setMinimumHeight(220)
        self.history_list.setSpacing(6)
        self.history_list.setFont(QtGui.QFont("Segoe UI", 10))
        left.addWidget(self.history_list)

        # action buttons row
        actions = QtWidgets.QHBoxLayout()
        self.btn_refresh = QtWidgets.QPushButton("Refresh Data")
        self.btn_admin = QtWidgets.QPushButton("Open Backend Admin")
        self.btn_export = QtWidgets.QPushButton("Export Report (PDF)")
        self.btn_export.setObjectName("primaryBtn")
        actions.addWidget(self.btn_refresh)
        actions.addWidget(self.btn_admin)
        actions.addStretch(1)
        actions.addWidget(self.btn_export)
        left.addLayout(actions)

        # bind actions
        self.btn_refresh.clicked.connect(self.fetch_all)
        self.btn_admin.clicked.connect(self.open_admin)
        self.btn_export.clicked.connect(self.export_report)

      
        right = QtWidgets.QVBoxLayout()
        right.setSpacing(12)
        content.addLayout(right, 64)

      
        donut_frame = QtWidgets.QFrame()
        donut_frame.setStyleSheet("background:transparent;")
        donut_layout = QtWidgets.QHBoxLayout(donut_frame)
        donut_layout.setContentsMargins(6, 6, 6, 6)

       
        self.donut_canvas = ChartCanvas(width=7, height=5, dpi=100)
        donut_layout.addWidget(self.donut_canvas, 7)

      
        self.legend_container = QtWidgets.QFrame()
        self.legend_container.setStyleSheet("background:white; border-radius:8px; padding:10px;")
        legend_layout = QtWidgets.QVBoxLayout(self.legend_container)
        legend_layout.setContentsMargins(6, 6, 6, 6)
        legend_title = QtWidgets.QLabel("Equipment Distribution")
        legend_title.setStyleSheet("font-weight:700;")
        legend_layout.addWidget(legend_title)
        self.legend_box = QtWidgets.QVBoxLayout()
        legend_layout.addLayout(self.legend_box)
        donut_layout.addWidget(self.legend_container, 3)

        right.addWidget(donut_frame, 6)

        # bar chart
        bar_frame = QtWidgets.QFrame()
        bar_frame.setStyleSheet("background:white; border-radius:10px; padding:8px;")
        b_layout = QtWidgets.QVBoxLayout(bar_frame)
        title_bar = QtWidgets.QLabel("Averages (Flowrate, Pressure, Temperature)")
        title_bar.setStyleSheet("font-weight:700;")
        b_layout.addWidget(title_bar)
        self.bar_canvas = ChartCanvas(width=7, height=2.6, dpi=100)
        b_layout.addWidget(self.bar_canvas)
        right.addWidget(bar_frame, 4)

     
        copyright_label = QtWidgets.QLabel("Built with PyQt5 • Demo Local (not deployed)")
        copyright_label.setStyleSheet("color:#999; font-size:11px;")
        root.addWidget(copyright_label, alignment=Qt.AlignRight)

  
        self.setStyleSheet(self._global_qss())

    def _global_qss(self):
        return """
        QPushButton#primaryBtn, QPushButton#primaryBtnLarge {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #2b8cbe, stop:1 #2b6ea8);
            color: white;
            border: none;
            padding: 8px 14px;
            border-radius: 8px;
            font-weight:600;
        }
        QPushButton#chooseBtn {
            background: #fff;
            border: 1px solid #e6e9ec;
            padding:8px 12px;
            border-radius:8px;
        }
        QPushButton:hover { background: #f3fbff; }
        QListWidget { outline: none; }
        """

    def _make_kpi_card(self, title, value):
        card = HoverCard()
        card.setStyleSheet("background:white; border-radius:10px;")
        v = QtWidgets.QVBoxLayout(card)
        v.setContentsMargins(12, 10, 12, 10)
        lbl_title = QtWidgets.QLabel(title)
        lbl_title.setStyleSheet("color:#666; font-size:12px;")
        lbl_val = QtWidgets.QLabel(value)
        lbl_val.setStyleSheet("color:#0b4f6c; font-size:26px; font-weight:800;")
        lbl_val.setAlignment(Qt.AlignCenter)
        v.addWidget(lbl_title)
        v.addSpacing(6)
        v.addWidget(lbl_val)
      
        card._value_label = lbl_val
        return card

    # ---------------- File selection & upload ----------------
    def choose_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select CSV file", "", "CSV files (*.csv)")
        if path:
            self.file_path = path
            self.lbl_file.setText(os.path.basename(path))

    def upload_file(self):
        if not self.file_path:
            self.sig_status.emit("Select a CSV first")
            return

        @threaded
        def job(filepath):
            self.sig_status.emit("Uploading...")
            try:
                with open(filepath, "rb") as fh:
                    files = {"file": (os.path.basename(filepath), fh, "text/csv")}
                    resp = requests.post(API_UPLOAD, headers=HEADERS, files=files, timeout=20)
                if resp.status_code in (200, 201):
                    self.sig_status.emit("Upload successful — refreshing")
                    self.fetch_all()
                else:
                    self.sig_status.emit(f"Upload failed: {resp.status_code}")
            except Exception as e:
                self.sig_status.emit(f"Upload error: {e}")

        job(self.file_path)

    # ---------------- Data fetch (background) ----------------
    def fetch_all(self):
        self.sig_status.emit("Refreshing data...")
        self._fetch_latest()
        self._fetch_history()

    @threaded
    def _fetch_latest(self):
        try:
            resp = requests.get(API_LATEST, headers=HEADERS, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                summary = data.get("summary") if isinstance(data, dict) and "summary" in data else data
                self.sig_summary.emit(summary)
                self.sig_status.emit("Latest summary loaded")
            else:
                self.sig_status.emit(f"Latest failed: {resp.status_code}")
        except Exception as e:
            self.sig_status.emit(f"Latest error: {e}")

    @threaded
    def _fetch_history(self):
        try:
            resp = requests.get(API_HISTORY, headers=HEADERS, timeout=12)
            if resp.status_code == 200:
                arr = resp.json() or []
                self.sig_history.emit(arr)
                self.sig_status.emit("History loaded")
            else:
                self.sig_status.emit(f"History failed: {resp.status_code}")
        except Exception as e:
            self.sig_status.emit(f"History error: {e}")

   
    def _on_status(self, txt):
        self.status_label.setText(str(txt))

    def _on_history(self, arr):
        self.history_list.clear()
        if not arr:
            self.history_list.addItem("No uploads found.")
            return
 
        for i, item in enumerate(arr[:5]):
            ds_id = item.get("id", item.get("dataset_id", "N/A"))
            uploaded_at = item.get("uploaded_at") or item.get("created_at") or item.get("uploaded_at_iso") or ""
            display = f"ID {ds_id}  •  {uploaded_at}"
            list_item = QtWidgets.QListWidgetItem(display)
            list_item.setFont(QtGui.QFont("Segoe UI", 10))
            self.history_list.addItem(list_item)
            
            if i == 0:
                try:
                    self.latest_dataset_id = int(ds_id)
                except:
                    self.latest_dataset_id = ds_id

    def _on_summary(self, summary):
        if not summary:
            self.summary_text.setText("No summary available.")
            return

        # parse summary
        total = summary.get("total_count", summary.get("total", 0))
        averages = summary.get("averages", {})
        dist = summary.get("type_distribution", {})

        # KPI cards (bolder & darker)
        self.card_total._value_label.setText(str(total))
        self.card_flow._value_label.setText(f"{averages.get('Flowrate', 0):.2f}")
        self.card_pressure._value_label.setText(f"{averages.get('Pressure', 0):.2f}")
        self.card_temp._value_label.setText(f"{averages.get('Temperature', 0):.2f}")

        # summary rich text
        s = (
            f"<div style='font-size:13px;color:#333;'>"
            f"Total Records: <b style='font-size:15px;color:#0b4f6c;'>{total}</b><br>"
            f"Average Flowrate: <b style='font-size:13px;color:#0b4f6c;'>{averages.get('Flowrate',0):.2f}</b><br>"
            f"Average Pressure: <b style='font-size:13px;color:#0b4f6c;'>{averages.get('Pressure',0):.2f}</b><br>"
            f"Average Temperature: <b style='font-size:13px;color:#0b4f6c;'>{averages.get('Temperature',0):.2f}</b>"
            f"</div>"
        )
        self.summary_text.setText(s)

        # draw donut (big)
        self._draw_donut(dist, total)

        # draw bar
        self._draw_bar(averages)

    # ---------------- Chart drawing ----------------
    def _draw_donut(self, dist, total):
        ax = self.donut_canvas.axes
        ax.clear()
        labels = list(dist.keys())
        sizes = list(dist.values())
        if not labels or sum(sizes) == 0:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=14)
            self.donut_canvas.draw()
            return

        colors = PALETTE * (len(labels) // len(PALETTE) + 1)
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=None,
            colors=colors[:len(labels)],
            wedgeprops=dict(width=0.48, edgecolor='white'),
            startangle=90,
            autopct='%1.0f%%',
            pctdistance=0.78,
            textprops={'fontsize': 10}
        )
        # center total
        ax.text(0, 0, str(total), ha='center', va='center', fontsize=20, fontweight=800, color="#0b4f6c")
        ax.set_aspect('equal')
        ax.axis('off')

        # update legend box on the right (clear and repopulate)
        while self.legend_box.count():
            item = self.legend_box.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        for i, lab in enumerate(labels):
            row = QtWidgets.QHBoxLayout()
            pill = QtWidgets.QLabel()
            pill.setFixedSize(12, 12)
            pill.setStyleSheet(f"background:{colors[i]}; border-radius:3px;")
            txt = QtWidgets.QLabel(lab)
            txt.setStyleSheet("font-size:12px; padding-left:8px;")
            row.addWidget(pill)
            row.addWidget(txt)
            row.addStretch()
            self.legend_box.addLayout(row)

        self.donut_canvas.draw()

    def _draw_bar(self, averages):
        ax = self.bar_canvas.axes
        ax.clear()
        keys = ["Flowrate", "Pressure", "Temperature"]
        vals = [float(averages.get(k, 0) or 0) for k in keys]
        maxv = max(vals) if vals else 1
        if maxv <= 0:
            maxv = 1
        bars = ax.bar(keys, vals, color="#2b8cbe", edgecolor="white", width=0.5)
        ax.set_ylim(0, maxv * 1.25)
        ax.grid(axis='y', linestyle='--', alpha=0.25)
        ax.set_ylabel("")
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2.0, v + (maxv * 0.03), f"{v:.2f}", ha="center", va="bottom", fontsize=10, fontweight=700)
        self.bar_canvas.draw()

   
    def open_admin(self):
        try:
            webbrowser.open("http://127.0.0.1:8000/admin/")
        except Exception as e:
            self.sig_status.emit(f"Open admin error: {e}")

    def export_report(self):
        if not self.latest_dataset_id:
            self.sig_status.emit("No dataset id found. Refresh and try.")
            return

        @threaded
        def job(ds_id):
            self.sig_status.emit("Requesting report...")
            url = API_REPORT.format(id=ds_id)
            try:
                resp = requests.get(url, headers=HEADERS, timeout=20, stream=True)
                if resp.status_code == 200:
                    fname = f"dataset_report_{ds_id}.pdf"
                    with open(fname, "wb") as fh:
                        for chunk in resp.iter_content(8192):
                            if chunk:
                                fh.write(chunk)
                    self.sig_status.emit(f"Report saved: {fname}")
                    # open file automatically after download
                    try:
                        if sys.platform.startswith("win"):
                            os.startfile(fname)
                        else:
                            webbrowser.open(fname)
                    except Exception:
                        pass
                else:
                    self.sig_status.emit(f"Export failed: {resp.status_code}")
            except Exception as e:
                self.sig_status.emit(f"Export error: {e}")

        job(self.latest_dataset_id)


def main():
    app = QtWidgets.QApplication(sys.argv)
    
    app.setFont(QtGui.QFont("Segoe UI", 10))
    w = DesktopApp()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
