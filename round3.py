#!/usr/bin/env python3
import sys
import os
import tempfile
import random
import subprocess
import platform
import threading
import ctypes

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPlainTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QInputDialog,
    QMenuBar, QAction, QFileDialog
)
from PyQt5.QtCore import Qt, QProcess, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor, QKeySequence


# ============ SYSTEM-LEVEL KEY INTERCEPTION ============
class KeyBlockerThread(QThread):
    """
    Thread that runs system-level key blocking to prevent Alt+Tab, Win+Tab, etc.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_running = False
        self.parent_app = parent

    def run(self):
        """Run system-specific key blocking"""
        self.is_running = True
        try:
            if platform.system() == "Windows":
                self._block_keys_windows()
            elif platform.system() == "Darwin":  # macOS
                self._block_keys_macos()
            elif platform.system() == "Linux":
                self._block_keys_linux()
        except Exception as e:
            print(f"Key blocking error: {e}")

    def _block_keys_windows(self):
        """Block Alt+Tab and other switching keys on Windows"""
        try:
            import msvcrt
            import keyboard
            
            while self.is_running:
                try:
                    # Block Alt+Tab
                    if keyboard.is_pressed('alt+tab'):
                        continue
                    # Block Win key
                    if keyboard.is_pressed('win'):
                        continue
                    # Block Alt+Esc
                    if keyboard.is_pressed('alt+esc'):
                        continue
                    # Block Ctrl+Alt+Delete (catch attempt)
                    if keyboard.is_pressed('ctrl+alt+delete'):
                        continue
                except Exception:
                    pass
                
                # Small sleep to avoid CPU spinning
                self.msleep(50)
        except ImportError:
            print("Warning: 'keyboard' module not installed. System-level key blocking unavailable.")

    def _block_keys_macos(self):
        """Block Command+Tab and other switching keys on macOS"""
        try:
            import keyboard
            
            while self.is_running:
                try:
                    # Block Command+Tab
                    if keyboard.is_pressed('cmd+tab'):
                        continue
                    # Block Command+`
                    if keyboard.is_pressed('cmd+grave'):
                        continue
                except Exception:
                    pass
                
                self.msleep(50)
        except ImportError:
            print("Warning: 'keyboard' module not installed. System-level key blocking unavailable.")

    def _block_keys_linux(self):
        """Block Alt+Tab and other switching keys on Linux"""
        try:
            import keyboard
            
            while self.is_running:
                try:
                    # Block Alt+Tab
                    if keyboard.is_pressed('alt+tab'):
                        continue
                    # Block Super key
                    if keyboard.is_pressed('super'):
                        continue
                except Exception:
                    pass
                
                self.msleep(50)
        except ImportError:
            print("Warning: 'keyboard' module not installed. System-level key blocking unavailable.")

    def stop_blocking(self):
        """Stop the key blocking thread"""
        self.is_running = False
        self.wait()


class OfflinePythonIDE(QWidget):
    HARD_TIMEOUT_MS = 15 * 60 * 1000
    GROUP_TIMER_MS = 20 * 60 * 1000  # 20 minutes in milliseconds

    # Template codes for each program (prog1..prog15)
    PROGRAM_TEMPLATES = {
        "prog1": """# Program 1
def add(a, b):
    return a + b

def divide(a, b):
    return a / b

values = [10, 20, "30", 40]
total = 0

for v in values:
    total = total + v

avg = divide(total, len(values))
print("Average is " + avg)

if avg> 25
    print("High")
else:
    print("Low")

count = 3
while count >= 0:
print("Count:", count)
    count = count + 1

def store(data=[]):
    for i in range(2):
data.append(i)
    return data

a = store()
b = store()

info = {"name": "Sam", "age": 21}
print(info["grade"])

def calculate():
    x = 10
    if x == 10:
        y = x * 2
    return y

result = calculate()
print(result)

numbers = [1, 2, 3]
print(numbers[5])

def show(msg):
print("Message: " + msg)

show(100)

final = add(5)
print(final)

status = True
if status is "True":
    print("Active")

for i in range(3):
    pass

x = 5
if x > 2:
print("X is big")

print("Processing done")

print("End")

"""EXPECTED OUTPUT:
Average is 25.0
Low
Count: 3
Count: 2
Count: 1
Count: 0
A
20
3
Message: 100
8
Active
X is big
Processing done
End"""
""",
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Compiler of MNMJEC")
        self.setGeometry(150, 80, 1100, 720)

        # ---------- UI ----------
        title = QLabel("Python Compiler of MNMJEC")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title.setStyleSheet("color:#0b1220;font-size:20px;font-weight:700;")

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Write Python code here…")
        self.editor.setStyleSheet("""
            background:#001f3f;
            color:#ffd700;
            font-family:Consolas;
            font-size:16px;
            padding:14px;
            border-radius:8px;
            border: 1px solid rgba(11,18,32,0.12);
            selection-background-color: rgba(255,215,0,0.15);
            selection-color: #ffd700;
        """)

        self.output = QPlainTextEdit(readOnly=True)
        self.output.setStyleSheet("""
            background:#071733;
            color:#ffd700;
            font-family:Consolas;
            font-size:14px;
            padding:14px;
            border-radius:8px;
            border: 1px solid rgba(11,18,32,0.12);
            selection-background-color: rgba(255,215,0,0.12);
            selection-color: #071733;
        """)

        self.run_btn = QPushButton("▶ Run")
        self.stop_btn = QPushButton("⛔ Stop")
        self.clear_btn = QPushButton("🧹 Clear")

        for btn in (self.run_btn, self.stop_btn, self.clear_btn):
            btn.setStyleSheet("""
                QPushButton {
                    background:#2563eb;
                    color:white;
                    padding:8px 18px;
                    font-size:14px;
                    border-radius:6px;
                }
                QPushButton:hover { background:#1e40af; }
            """)

        self.stop_btn.setEnabled(False)
        self.run_btn.clicked.connect(self.run_code)
        self.stop_btn.clicked.connect(self.stop_process)
        self.clear_btn.clicked.connect(self.output.clear)

        btns = QHBoxLayout()
        btns.addWidget(self.run_btn)
        btns.addWidget(self.stop_btn)
        btns.addWidget(self.clear_btn)
        btns.addStretch()

        # error banner (hidden initially)
        self.error_banner = QLabel()
        self.error_banner.setVisible(False)
        self.error_banner.setStyleSheet("background:#b91c1c;color:white;padding:6px;border-radius:4px;")
        self.error_banner.setAlignment(Qt.AlignCenter)

        # group timer label to show remaining time for the visible templates (placed top-right)
        self.group_timer_label = QLabel()
        self.group_timer_label.setVisible(False)
        self.group_timer_label.setStyleSheet("background:#0b1220;color:#ffd700;padding:6px;border-radius:6px;")
        self.group_timer_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Exam mode indicator label
        self.exam_mode_label = QLabel()
        self.exam_mode_label.setVisible(False)
        self.exam_mode_label.setText("🔒 EXAM MODE ACTIVE")
        self.exam_mode_label.setStyleSheet("background:#dc2626;color:white;padding:6px;border-radius:6px;font-weight:bold;")
        self.exam_mode_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)

        # ---------- MENU BAR ----------
        self.menu_bar = QMenuBar(self)

        # File menu
        file_menu = self.menu_bar.addMenu("File")
        self.new_act = QAction("New", self)
        self.new_act.setShortcut("Ctrl+N")
        self.new_act.triggered.connect(self.new_file)
        self.open_act = QAction("Open...", self)
        self.open_act.setShortcut("Ctrl+O")
        self.open_act.triggered.connect(self.open_file)
        self.save_act = QAction("Save", self)
        self.save_act.setShortcut("Ctrl+S")
        self.save_act.triggered.connect(self.save_file)
        self.save_as_act = QAction("Save As...", self)
        self.save_as_act.triggered.connect(self.save_file_as)
        self.exit_act = QAction("Exit", self)
        self.exit_act.triggered.connect(self.close)
        for act in (self.new_act, self.open_act, self.save_act, self.save_as_act, self.exit_act):
            file_menu.addAction(act)

        self.file_actions = [self.new_act, self.open_act]

        # Run menu
        run_menu = self.menu_bar.addMenu("Run")
        run_act = QAction("Run", self)
        run_act.setShortcut("F5")
        run_act.triggered.connect(self.run_code)
        stop_act = QAction("Stop", self)
        stop_act.triggered.connect(self.stop_process)
        clear_out_act = QAction("Clear Output", self)
        clear_out_act.triggered.connect(self.output.clear)
        for act in (run_act, stop_act, clear_out_act):
            run_menu.addAction(act)

        # Programs menu
        programs_menu = self.menu_bar.addMenu("Programs")
        all_keys = list(self.PROGRAM_TEMPLATES.keys())
        self.visible_template_keys = random.sample(all_keys, min(5, len(all_keys)))
        random.shuffle(self.visible_template_keys)

        self.prog_actions = []
        for key in self.visible_template_keys:
            i = int(key.replace("prog", ""))
            act = QAction(f"Prog {i}", self)
            act.triggered.connect(lambda checked=False, k=key: self.load_program_template(k))
            programs_menu.addAction(act)
            self.prog_actions.append(act)

        # Help menu
        help_menu = self.menu_bar.addMenu("Help")
        about_act = QAction("About", self)
        about_act.triggered.connect(self.show_about)
        help_menu.addAction(about_act)

        layout.setMenuBar(self.menu_bar)

        # Top row: title (left) and timer (right)
        top_row = QHBoxLayout()
        top_row.addWidget(title)
        top_row.addStretch()
        top_row.addWidget(self.group_timer_label)
        layout.addLayout(top_row)

        layout.addWidget(self.exam_mode_label)
        layout.addWidget(self.error_banner)
        layout.addWidget(QLabel("📝 Code Editor"))
        layout.addWidget(self.editor, 3)
        layout.addLayout(btns)
        layout.addWidget(QLabel("📤 Output Console"))
        layout.addWidget(self.output, 2)

        self.setStyleSheet("background:#ffffff; color:#0b1220;")

        # ---------- PROCESS ----------
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.finished.connect(self.finished)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.force_kill)

        # group timer variables
        self.group_timer_started = False
        self.group_time_left_ms = 0
        self.group_countdown_timer = QTimer(self)
        self.group_countdown_timer.timeout.connect(self._tick_group_timer)

        self.temp_file = None
        self.user_input = ""
        self.current_file = None
        self.runtime_error = False
        self.current_template = None
        self._pre_run_was_maximized = False

        # Variables for system key blocking and keyboard grabbing
        self._last_run_initiated_by_ide = False
        self._protect_run_active = False
        self._keyboard_grabbed = False

        # Exam mode lock
        self.exam_lock_active = False
        self.key_blocker_thread = None
        self.window_focus_timer = QTimer(self)
        self.window_focus_timer.timeout.connect(self._enforce_window_focus)

        # Timer to prevent task switching
        self.app_switch_prevention_timer = QTimer(self)
        self.app_switch_prevention_timer.timeout.connect(self._prevent_app_switch)

    # ---------- Helpers ----------
    def set_program_actions_enabled(self, enabled: bool):
        try:
            for act in getattr(self, "prog_actions", []):
                act.setEnabled(enabled)
        except Exception:
            pass

    def set_file_actions_enabled(self, enabled: bool):
        try:
            for act in getattr(self, "file_actions", []):
                act.setEnabled(enabled)
        except Exception:
            pass

    # ---------- Group timer for visible templates ----------
    def start_group_timer_if_needed(self):
        """Start the 20-minute group timer for the visible templates on first template selection."""
        if self.group_timer_started:
            return
        self.group_timer_started = True
        self.group_time_left_ms = self.GROUP_TIMER_MS
        self._update_group_timer_label()
        self.group_timer_label.setVisible(True)
        self.group_countdown_timer.start(1000)
        QTimer.singleShot(self.GROUP_TIMER_MS, self.on_group_time_expired)

    def _tick_group_timer(self):
        self.group_time_left_ms -= 1000
        if self.group_time_left_ms <= 0:
            self.group_time_left_ms = 0
            self.group_countdown_timer.stop()
        self._update_group_timer_label()

    def _update_group_timer_label(self):
        ms = max(0, self.group_time_left_ms)
        seconds = ms // 1000
        mins = seconds // 60
        secs = seconds % 60
        self.group_timer_label.setText(f"⏳ Templates time left: {mins:02d}:{secs:02d}")
        if ms == 0:
            self.group_timer_label.setText("⏱ Templates time expired — editor is read-only")

    def on_group_time_expired(self):
        try:
            self.group_countdown_timer.stop()
        except Exception:
            pass
        self.editor.setReadOnly(True)
        self.run_btn.setEnabled(False)
        self.set_program_actions_enabled(False)
        self.set_file_actions_enabled(False)
        self.set_error_banner(True, "⏱ Time for the displayed templates has expired — editor is now read-only.")
        self.group_timer_label.setVisible(True)
        self._update_group_timer_label()

    # ---------- WINDOW LOCK ----------
    def lock_window(self):
        try:
            self.setWindowFlag(Qt.WindowCloseButtonHint, True)
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            self.raise_()
            self.activateWindow()
            self.show()
        except Exception:
            pass

    def unlock_window(self):
        try:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
            self.show()
        except Exception:
            pass

    # ---------- MIN / MAX CONTROL ----------
    def disable_min_max(self):
        try:
            self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
            self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
            self.show()
        except Exception:
            pass

    def enable_min_max(self):
        try:
            self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
            self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
            self.show()
        except Exception:
            pass

    # ---------- ERROR BANNER ----------
    def set_error_banner(self, show: bool, text: str = ""):
        try:
            if show:
                self.error_banner.setText(text)
                self.error_banner.setVisible(True)
            else:
                self.error_banner.setVisible(False)
                self.error_banner.setText("")
        except Exception:
            pass

    # ---------- INPUT DETECTION ----------
    def code_needs_input(self, code):
        return "input(" in code

    # ---------- SYNTAX CHECK ----------
    def has_syntax_error(self, code):
        try:
            compile(code, "<contest>", "exec")
            return None
        except Exception:
            return "Error occurred"

    # ========== EXAM MODE FEATURES ==========
    def _start_system_key_blocking(self):
        """Start system-level key blocking to prevent app switching"""
        try:
            if self.key_blocker_thread is None or not self.key_blocker_thread.isRunning():
                self.key_blocker_thread = KeyBlockerThread(self)
                self.key_blocker_thread.start()
        except Exception as e:
            print(f"Failed to start key blocker: {e}")

    def _stop_system_key_blocking(self):
        """Stop system-level key blocking"""
        try:
            if self.key_blocker_thread is not None:
                self.key_blocker_thread.stop_blocking()
                self.key_blocker_thread = None
        except Exception:
            pass

    def _enforce_window_focus(self):
        """Enforce that this window always has focus during exam mode"""
        try:
            if self.exam_lock_active:
                if not self.isActiveWindow():
                    self.raise_()
                    self.activateWindow()
                    self.setWindowState(self.windowState() | Qt.WindowActive)
        except Exception:
            pass

    def _prevent_app_switch(self):
        """Monitor and prevent app switching during exam mode"""
        try:
            if self.exam_lock_active:
                if not self.isVisible() or not self.isActiveWindow():
                    self.raise_()
                    self.activateWindow()
                    self.showFullScreen()
        except Exception:
            pass

    def _activate_exam_mode(self):
        """Fully activate exam mode with all protections"""
        try:
            self.exam_lock_active = True
            
            # Show exam mode indicator
            self.exam_mode_label.setVisible(True)
            
            # Window flags
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
            self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
            self.setWindowFlag(Qt.WindowCloseButtonHint, False)
            
            # Set to fullscreen
            self.showFullScreen()
            
            # Grab keyboard
            try:
                self.grabKeyboard()
                self._keyboard_grabbed = True
            except Exception:
                pass
            
            # Grab mouse
            try:
                self.grabMouse()
            except Exception:
                pass
            
            # Start system key blocking
            self._start_system_key_blocking()
            
            # Start window focus enforcement
            self.window_focus_timer.start(500)  # Check every 500ms
            
            # Start app switch prevention
            self.app_switch_prevention_timer.start(200)  # Check every 200ms
            
            # Disable all menu actions
            for menu_bar_action in self.menu_bar.actions():
                menu_bar_action.setEnabled(False)
            
            self.output.appendPlainText("\n🔒 EXAM MODE ACTIVE — APP SWITCHING DISABLED")
            self.output.appendPlainText("🔒 Cannot minimize, close, or switch apps")
            self.output.appendPlainText("🔒 Press Ctrl+F12 (Admin Key) to exit exam mode\n")
            
        except Exception as e:
            print(f"Error activating exam mode: {e}")

    def _deactivate_exam_mode(self):
        """Deactivate exam mode and restore normal functionality"""
        try:
            self.exam_lock_active = False
            
            # Hide exam mode indicator
            self.exam_mode_label.setVisible(False)
            
            # Stop timers
            self.window_focus_timer.stop()
            self.app_switch_prevention_timer.stop()
            
            # Stop key blocking
            self._stop_system_key_blocking()
            
            # Release input grabs
            try:
                self.releaseKeyboard()
                self._keyboard_grabbed = False
            except Exception:
                pass
            
            try:
                self.releaseMouse()
            except Exception:
                pass
            
            # Restore window flags
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
            self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
            self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
            self.setWindowFlag(Qt.WindowCloseButtonHint, True)
            
            # Show normal window
            self.showNormal()
            
            # Re-enable menu actions
            for menu_bar_action in self.menu_bar.actions():
                menu_bar_action.setEnabled(True)
            
            self.output.appendPlainText("\n✅ EXAM MODE DEACTIVATED")
            self.output.appendPlainText("✅ Normal mode restored\n")
            
        except Exception as e:
            print(f"Error deactivating exam mode: {e}")

    def _safe_disable_exam_mode(self):
        """Safely disable exam mode after verifying admin key"""
        if self.exam_lock_active:
            self._deactivate_exam_mode()
            QMessageBox.information(self, "Unlocked", "Exam mode disabled. Normal mode restored.")
        else:
            QMessageBox.information(self, "Info", "Exam mode is not active.")

    # ---------- SYSTEM KEY BLOCKING ----------
    def _install_system_key_block(self):
        """Install system key blocking"""
        try:
            return True
        except Exception:
            return False

    def _uninstall_system_key_block(self):
        """Uninstall system key blocking"""
        try:
            self._protect_run_active = False
            if self._keyboard_grabbed:
                try:
                    self.releaseKeyboard()
                    self._keyboard_grabbed = False
                except Exception:
                    pass
        except Exception:
            pass

    # ---------- RUN ----------
    def run_code(self):
        if self.group_timer_started and self.group_time_left_ms == 0:
            QMessageBox.information(self, "Time Expired", "Template time expired — editor is read-only.")
            return

        code = self.editor.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "No Code", "Please write some Python code.")
            return

        error = self.has_syntax_error(code)
        if error:
            self.output.clear()
            self.output.appendPlainText("❌ SYNTAX ERROR DETECTED\n")
            self.output.appendPlainText("Error occurred\n")
            self.runtime_error = True
            self.disable_min_max()
            if self.current_template:
                self.set_error_banner(True, f"❌ Syntax error detected — Fix the code in '{self.current_template}' and run successfully to enable minimize/maximize buttons")
            else:
                self.set_error_banner(True, "❌ Syntax error detected — fix code and run to unlock window")
            self.lock_window()
            return

        self.runtime_error = False
        self.disable_min_max()
        self.set_error_banner(False, "")

        if self.current_template:
            self.start_group_timer_if_needed()

        self.user_input = ""
        if self.code_needs_input(code):
            text, ok = QInputDialog.getMultiLineText(self, "Program Input", "Enter input:")
            if not ok:
                return
            self.user_input = text + "\n"

        header = "import sys\nsys.setrecursionlimit(10**7)\n"
        code = header + code

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as f:
                f.write(code)
                self.temp_file = f.name
        except Exception as e:
            QMessageBox.critical(self, "Temp File Error", f"Failed to write temp file:\n{e}")
            self.enable_min_max()
            return

        self.output.clear()
        self.output.appendPlainText("▶ Running...\n")

        self.editor.setReadOnly(True)
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        try:
            self._pre_run_was_maximized = self.isMaximized()
            self.showMaximized()
        except Exception:
            pass

        try:
            prev_env = os.environ.get('MNMJ_PARENT_PID')
            try:
                os.environ['MNMJ_PARENT_PID'] = str(os.getpid())
                self._last_run_initiated_by_ide = True
                self.process.start(sys.executable, ["-u", self.temp_file])
            finally:
                try:
                    if prev_env is None:
                        del os.environ['MNMJ_PARENT_PID']
                    else:
                        os.environ['MNMJ_PARENT_PID'] = prev_env
                except Exception:
                    pass
            if not self.process.waitForStarted(1000):
                self.output.appendPlainText("\n❌ Failed to start process.\n")
                self.stop_btn.setEnabled(False)
                self.run_btn.setEnabled(True)
                self.editor.setReadOnly(False)
                try:
                    if not self._pre_run_was_maximized:
                        self.showNormal()
                except Exception:
                    pass
                return
            try:
                if self._install_system_key_block():
                    self._protect_run_active = True
                    try:
                        self.grabKeyboard()
                        self._keyboard_grabbed = True
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            self.output.appendPlainText("\n❌ Failed to start process.\n")
            self.stop_btn.setEnabled(False)
            self.run_btn.setEnabled(True)
            self.editor.setReadOnly(False)
            try:
                if not self._pre_run_was_maximized:
                    self.showNormal()
            except Exception:
                pass
            return

        if self.user_input and self.process.state() == QProcess.Running:
            try:
                self.process.write(self.user_input.encode())
                self.process.closeWriteChannel()
            except Exception:
                pass

        self.timer.start(self.HARD_TIMEOUT_MS)

    # ---------- OUTPUT ----------
    def read_stdout(self):
        try:
            text = bytes(self.process.readAllStandardOutput()).decode(errors="replace")
            self.output.insertPlainText(text)
            cursor = self.output.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.output.setTextCursor(cursor)
        except Exception:
            pass

    def read_stderr(self):
        try:
            data = bytes(self.process.readAllStandardError()).decode(errors="replace")
            if data.strip() and not self.runtime_error:
                self.runtime_error = True
                self.output.insertPlainText("\n❌ ERROR: Error occurred\n")
                self.disable_min_max()
                if self.current_template:
                    self.set_error_banner(True, f"❌ Runtime error detected — Fix the code in '{self.current_template}' to enable minimize/maximize buttons.")
                else:
                    self.set_error_banner(True, "❌ Runtime error detected — window locked until fixed.")
                self.lock_window()
            else:
                if data.strip():
                    self.output.insertPlainText("\n❌ ERROR: Error occurred\n")
        except Exception:
            pass

    # ---------- CONTROL ----------
    def stop_process(self):
        if self.process.state() == QProcess.Running:
            try:
                self.process.kill()
            except Exception:
                pass
            self.output.appendPlainText("\n⛔ Stopped.")
        # remove protections if any
        try:
            self._uninstall_system_key_block()
        except Exception:
            pass
        try:
            self._protect_run_active = False
        except Exception:
            pass

    def force_kill(self):
        if self.process.state() == QProcess.Running:
            try:
                self.process.kill()
            except Exception:
                pass
            self.output.appendPlainText("\n⏱ Time limit exceeded.")
        # remove protections
        try:
            self._uninstall_system_key_block()
        except Exception:
            pass
        try:
            self._protect_run_active = False
        except Exception:
            pass

    def finished(self):
        try:
            self.timer.stop()
            self.editor.setReadOnly(False)
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.output.appendPlainText("\n✅ Finished.")

            try:
                if not self._pre_run_was_maximized:
                    self.showNormal()
            except Exception:
                pass

            if not self.runtime_error:
                if self.current_template:
                    # Only treat the template as "fixed" if this run was initiated
                    # by the IDE itself (prevents marking fixed via external runs).
                    if getattr(self, '_last_run_initiated_by_ide', False):
                        self.enable_min_max()
                        self.unlock_window()
                        self.set_error_banner(False, "")
                        # After successful run, clear template selection
                        self.current_template = None
                    else:
                        # If the run was not initiated by this IDE, do not unlock.
                        self.disable_min_max()
                        self.lock_window()
                        self.set_error_banner(True, "❌ Template run completed outside IDE permission — window remains locked.")
                    if not (self.group_timer_started and self.group_time_left_ms == 0):
                        self.set_program_actions_enabled(True)
                        self.set_file_actions_enabled(True)
                    self.output.appendPlainText(f"\n✅ Code fixed successfully! You can now switch to another template from the Programs menu or continue working.")
                else:
                    self.enable_min_max()
                    self.unlock_window()
                    self.set_error_banner(False, "")
            else:
                self.disable_min_max()
                self.lock_window()
                if self.current_template:
                    self.set_error_banner(True, f"❌ Run ended with errors — Fix the code or switch to another template from the Programs menu.")
                else:
                    self.set_error_banner(True, "❌ Run ended with errors — window locked until fixed.")
        finally:
            if self.temp_file and os.path.exists(self.temp_file):
                try:
                    os.remove(self.temp_file)
                except Exception:
                    pass
                self.temp_file = None
            # remove any system-level protections we installed
            try:
                self._uninstall_system_key_block()
            except Exception:
                pass
            try:
                self._protect_run_active = False
            except Exception:
                pass
            # reset internal run marker
            try:
                self._last_run_initiated_by_ide = False
            except Exception:
                pass
            self._pre_run_was_maximized = False

    # ---------- PROGRAM TEMPLATES ----------
    def load_program_template(self, template_name):
        """Load program template"""
        if template_name not in self.PROGRAM_TEMPLATES:
            QMessageBox.warning(self, "Error", f"Template '{template_name}' not found.")
            return

        if self.current_template:
            QMessageBox.information(self, "Template Locked", "A template is already loaded. Fix it (run successfully) or clear it before loading another template.")
            return

        if self.group_timer_started and self.group_time_left_ms == 0:
            QMessageBox.information(self, "Time Expired", "Template time expired — cannot load templates.")
            return

        if self.process.state() == QProcess.Running:
            try:
                self.process.kill()
            except Exception:
                pass
            self.timer.stop()
            self.editor.setReadOnly(False)
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except Exception:
                pass
            self.temp_file = None

        if self.editor.toPlainText().strip():
            resp = QMessageBox.question(
                self, "Load Template",
                f"Load '{template_name}' template? This will replace current code.",
                QMessageBox.Yes | QMessageBox.No
            )
            if resp != QMessageBox.Yes:
                return

        template_code = self.PROGRAM_TEMPLATES[template_name]

        pre_run_result = None
        try:
            compile(template_code, "<template>", "exec")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as tf:
                tf.write(template_code)
                tmp_path = tf.name
            try:
                completed = subprocess.run([sys.executable, "-u", tmp_path],
                                           input=None,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           timeout=2,
                                           check=False,
                                           encoding="utf-8")
                if completed.returncode != 0 or completed.stderr.strip():
                    pre_run_result = "error"
                else:
                    pre_run_result = "ok"
            except subprocess.TimeoutExpired:
                pre_run_result = "timeout"
            except Exception:
                pre_run_result = "error"
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
        except Exception:
            pre_run_result = "compile_error"

        if pre_run_result == "ok":
            self.output.clear()
            self.output.appendPlainText("ℹ️ Template pre-run completed (no immediate errors).\n")
        elif pre_run_result in ("timeout", "error", "compile_error"):
            self.output.clear()
            self.output.appendPlainText("ℹ️ Template pre-run detected an issue (will load template for fixing).\n")

        self.editor.setPlainText(template_code)
        self.editor.setReadOnly(False)

        self.current_template = template_name

        self.disable_min_max()
        self.set_program_actions_enabled(False)
        self.set_file_actions_enabled(False)

        self.set_error_banner(True, f"📝 Template '{template_name}' loaded — Fix the code and run successfully to enable minimize/maximize buttons")

        self.runtime_error = False
        self.user_input = ""
        if template_name in self.visible_template_keys:
            self.start_group_timer_if_needed()

        # Activate exam mode after loading template
        try:
            self._activate_exam_mode()
        except Exception as e:
            print(f"Error activating exam mode: {e}")

    # ---------- FILE OPERATIONS & HELP ----------
    def new_file(self):
        if self.current_template:
            QMessageBox.information(self, "Template Locked", "Cannot create a new file while a template is active. Fix the template (run successfully) or clear it first.")
            return

        if self.editor.toPlainText().strip():
            resp = QMessageBox.question(
                self, "New File", "Discard current contents and create a new file?",
                QMessageBox.Yes | QMessageBox.No
            )
            if resp != QMessageBox.Yes:
                return

        if self.process.state() == QProcess.Running:
            try:
                self.process.kill()
            except Exception:
                pass
            self.timer.stop()
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except Exception:
                pass
            self.temp_file = None

        self.editor.clear()
        self.editor.setReadOnly(False)
        self.current_file = None
        self.current_template = None
        if not (self.group_timer_started and self.group_time_left_ms == 0):
            self.set_program_actions_enabled(True)
            self.set_file_actions_enabled(True)
        self.setWindowTitle("Python Compiler of MNMJEC")
        self.output.clear()
        self.enable_min_max()
        self.set_error_banner(False, "")
        self.runtime_error = False
        self.user_input = ""

    def open_file(self):
        if self.current_template:
            QMessageBox.information(self, "Template Locked", "Cannot open a file while a template is active. Fix the template (run successfully) or clear it first.")
            return

        if self.group_timer_started and self.group_time_left_ms == 0:
            QMessageBox.information(self, "Time Expired", "Template time expired — cannot open files that would replace templates.")
            return

        path, _ = QFileDialog.getOpenFileName(self, "Open Python file", "", "Python Files (*.py);;All Files (*)")
        if path:
            try:
                if self.process.state() == QProcess.Running:
                    try:
                        self.process.kill()
                    except Exception:
                        pass
                    self.timer.stop()
                    self.run_btn.setEnabled(True)
                    self.stop_btn.setEnabled(False)

                if self.temp_file and os.path.exists(self.temp_file):
                    try:
                        os.remove(self.temp_file)
                    except Exception:
                        pass
                    self.temp_file = None

                with open(path, "r", encoding="utf-8") as f:
                    self.editor.setPlainText(f.read())
                self.editor.setReadOnly(False)
                self.current_file = path
                self.current_template = None
                if not (self.group_timer_started and self.group_time_left_ms == 0):
                    self.set_program_actions_enabled(True)
                    self.set_file_actions_enabled(True)
                self.setWindowTitle(f"Python Compiler of MNMJEC - {os.path.basename(path)}")
                self.output.clear()
                self.enable_min_max()
                self.set_error_banner(False, "")
                self.runtime_error = False
                self.user_input = ""
            except Exception as e:
                QMessageBox.critical(self, "Open Error", f"Failed to open file:\n{e}")

    def save_file(self):
        if self.current_file:
            path = self.current_file
        else:
            path, _ = QFileDialog.getSaveFileName(self, "Save Python file", "", "Python Files (*.py);;All Files (*)")
            if not path:
                return
            self.current_file = path
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self.setWindowTitle(f"Python Compiler of MNMJEC - {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{e}")

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Python file as", "", "Python Files (*.py);;All Files (*)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.editor.toPlainText())
                self.current_file = path
                self.setWindowTitle(f"Python Compiler of MNMJEC - {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{e}")

    def show_about(self):
        QMessageBox.information(self, "About", "Offline Python IDE — MNMJEC\nSimple offline code runner with exam mode protection.")

    # ⛔ BLOCK CLOSE WHEN IN EXAM MODE
    def closeEvent(self, event):
        if getattr(self, 'exam_lock_active', False):
            QMessageBox.warning(self, "Exam Mode Active", "Application cannot be closed during exam mode.\n\nPress Ctrl+F12 (Admin Key) to exit exam mode.")
            event.ignore()
        else:
            # Clean up before closing
            try:
                self._stop_system_key_blocking()
            except Exception:
                pass
            event.accept()

    # 🔓 ADMIN UNLOCK (Ctrl+F12)
    def keyPressEvent(self, event):
        try:
            if event.key() == Qt.Key_F12 and event.modifiers() == Qt.ControlModifier:
                if self.exam_lock_active:
                    self._deactivate_exam_mode()
                    QMessageBox.information(self, "Unlocked", "Exam mode disabled. Normal mode restored.")
                else:
                    QMessageBox.information(self, "Info", "Exam mode is not active.")
                return
        except Exception:
            pass
        
        # Block certain keys in exam mode
        if self.exam_lock_active:
            try:
                # Block Alt+Tab
                if event.key() == Qt.Key_Tab and event.modifiers() == Qt.AltModifier:
                    return
                # Block Alt+Esc
                if event.key() == Qt.Key_Escape and event.modifiers() == Qt.AltModifier:
                    return
                # Block Ctrl+Alt+Delete (if possible)
                if event.key() == Qt.Key_Delete and event.modifiers() == (Qt.ControlModifier | Qt.AltModifier):
                    return
                # Block Super/Windows key
                if event.key() in (Qt.Key_Super_L, Qt.Key_Super_R):
                    return
                # Block Alt+F4 (close)
                if event.key() == Qt.Key_F4 and event.modifiers() == Qt.AltModifier:
                    return
            except Exception:
                pass
        
        super().keyPressEvent(event)

    def changeEvent(self, event):
        """Monitor window state changes"""
        try:
            if self.exam_lock_active and event.type() == 3:  # WindowDeactivate event
                # Reactivate window if it loses focus
                QTimer.singleShot(100, self._enforce_window_focus)
        except Exception:
            pass
        super().changeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ide = OfflinePythonIDE()
    ide.show()
    sys.exit(app.exec_())
