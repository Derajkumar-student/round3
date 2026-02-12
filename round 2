#!/usr/bin/env python3
import sys
import os
import tempfile
import random
import subprocess
import ctypes
from ctypes import wintypes

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPlainTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QInputDialog,
    QMenuBar, QAction, QFileDialog
)
from PyQt5.QtCore import Qt, QProcess, QTimer
from PyQt5.QtGui import QTextCursor


class OfflinePythonIDE(QWidget):
    HARD_TIMEOUT_MS = 15 * 60 * 1000
    GROUP_TIMER_MS = 20 * 60 * 1000  # 20 minutes in milliseconds

    # Template codes for each program (prog1..prog15)
    PROGRAM_TEMPLATES = {
        "prog1": """# Program 1
def add(x, lst=__):
    if lst is None:
        lst = []
    lst.append(x)
    return lst
print(add(1))
print(add(2))
""",
        "prog2": """# Program 2
a = False
b = True
c = False
if a or b __ c:
    print("YES")
else:
    print("NO")
""",
        "prog3": """# Program 3
def register_user(user, users=None):
    if users is None:
        users = []
 if user ____ in users:
        users.append(user)
 return users
print(register_user("Alice")) 
print(register_user("Bob"))
""",
        "prog4": """# Program 4
funcs = []
for i in range(3):
    funcs.append(lambda:___ )
for f in funcs:
    print(f())
""",
        "prog5": """# Program 5
def make_funcs():
    return [lambda __: x for x in range(5)]
funcs = make_funcs()
print([f() for f in funcs])
""",
        "prog6": """# Program 6
 x = 7
if x __ 2 == 1:
    print("Odd")
else:
    print("Even")
""",
        "prog7": """# Program 7
funcs = []
for i in range(3):
    funcs.append(lambda:___ )
for f in funcs:
    print(f())
""",
        "prog8": """# Program 8
for i in range(1, 6):
    if i == 4:
        ______
    print(i)
""",
        "prog9": """# Program 9
def check_len(s):
    if len(s) >= 5:
        return "Long"
    return "Short"
_____________

""",
        "prog10": """# Program 10
list = [1, 2, 3]
def total(items):
    return ___(items)
print(total(list))
""",
        "prog11": """# Program 11
data = {"x": 10, "y": 20}
print(data.__("x"))
""",
        "prog12": """# Program 12
try:
    num = int("12a")
¬¬_______  ValueError:
    num = 0
print(num)
""",
        "prog13": """# Program 13
data = [1, 2, 2, 3, 4, 3]
result = []
for x in data:
    if x ___result:
        result.append(x)
print(result)
""",
        "prog14": """# Program 14
nums = [2, 4, 6]
total = 0
for n in nums:
    total __ n
print(total)
""",
        "prog15": """# Program 15
x = 10
def change():
    __ x
    x += 5
change()
print(x)
"""
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

        # Programs menu: show 5 templates chosen at random (in random order) each run of the IDE
        programs_menu = self.menu_bar.addMenu("Programs")
        all_keys = list(self.PROGRAM_TEMPLATES.keys())
        # choose 5 random templates to show this session
        self.visible_template_keys = random.sample(all_keys, 5)
        random.shuffle(self.visible_template_keys)

        self.prog_actions = []
        self.template_buttons = []  # Store template buttons for enable/disable control
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

        layout.addWidget(self.error_banner)
        
        # ---------- TEMPLATES PANEL ----------
        # Display available templates as quick-access buttons
        self.templates_panel_label = QLabel("📋 Available Templates (Click to Load)")
        layout.addWidget(self.templates_panel_label)
        templates_panel = QHBoxLayout()
        self.templates_panel_layout = templates_panel  # Store reference for later access
        
        for key in self.visible_template_keys:
            i = int(key.replace("prog", ""))
            btn = QPushButton(f"Template {i}")
            btn.setStyleSheet("""
                QPushButton {
                    background:#4f46e5;
                    color:white;
                    padding:10px 16px;
                    font-size:12px;
                    border-radius:6px;
                    border: 2px solid #4f46e5;
                    font-weight: bold;
                }
                QPushButton:hover { background:#4338ca; border: 2px solid #3730a3; }
                QPushButton:pressed { background:#3730a3; }
            """)
            btn.clicked.connect(lambda checked=False, k=key: self.load_program_template(k))
            templates_panel.addWidget(btn)
            self.template_buttons.append((btn, key))
        
        templates_panel.addStretch()
        self.templates_panel_widget = QWidget()  # Container for the layout
        self.templates_panel_widget.setLayout(templates_panel)
        layout.addWidget(self.templates_panel_widget)
        
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

        # Track whether window was maximized before a run so we can restore it later
        self._pre_run_was_maximized = False
        
        # Track if the last run was initiated by this IDE (used for validation)
        self._last_run_initiated_by_ide = False

        # System hook state and focus protection
        self._system_hook_installed = False
        self._hhook = None
        self._hook_proc_ptr = None
        self._protect_run_active = False
        # Track whether we've grabbed the keyboard to block switching
        self._keyboard_grabbed = False
        # Exam mode flag (admin unlock required)
        self.exam_lock_active = False
        # Halt mode flag (activated when template runs successfully with output)
        self.halt_mode_active = False
        # Track if output was produced during execution
        self.execution_output_produced = False
        try:
            app_instance = QApplication.instance()
            if app_instance is not None:
                app_instance.focusChanged.connect(self._on_focus_changed)
        except Exception:
            pass

        # Periodically check whether a debugger is attached; if so, enable protections
        try:
            self._debugger_check_timer = QTimer(self)
            self._debugger_check_timer.setInterval(1000)
            self._debugger_check_timer.timeout.connect(self._check_debugger_and_protect)
            self._debugger_check_timer.start()
        except Exception:
            self._debugger_check_timer = None

        # ========== NEW: ENHANCED WINDOW LOCK PROTECTION ==========
        # (hash and debugger locks removed)

    # ---------- Helpers ----------
    def _on_focus_changed(self, old, now):
        try:
            if getattr(self, '_protect_run_active', False):
                # If focus changed away from this IDE, try to restore it
                if now is not None and now.window() is not self:
                    QTimer.singleShot(50, lambda: (self.raise_(), self.activateWindow()))
        except Exception:
            pass

    def _install_system_key_block(self):
        """Install a low-level keyboard hook on Windows to block Alt+Tab / Win keys / Ctrl+Esc."""
        if os.name != 'nt':
            return False
        if self._system_hook_installed:
            return True
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            WH_KEYBOARD_LL = 13
            WM_KEYDOWN = 0x0100
            WM_KEYUP = 0x0101
            WM_SYSKEYDOWN = 0x0104
            WM_SYSKEYUP = 0x0105

            # KBDLLHOOKSTRUCT
            class KBDLLHOOKSTRUCT(ctypes.Structure):
                _fields_ = [
                    ('vkCode', wintypes.DWORD),
                    ('scanCode', wintypes.DWORD),
                    ('flags', wintypes.DWORD),
                    ('time', wintypes.DWORD),
                    ('dwExtraInfo', wintypes.ULONG_PTR),
                ]

            LowLevelKeyboardProc = ctypes.WINFUNCTYPE(wintypes.LRESULT, wintypes.INT, wintypes.WPARAM, wintypes.LPARAM)

            def _proc(nCode, wParam, lParam):
                try:
                    if nCode == 0:
                        kb = KBDLLHOOKSTRUCT.from_address(lParam)
                        vk = kb.vkCode
                        flags = kb.flags
                        alt_pressed = (flags & 0x20) != 0
                        # Block Win keys
                        if vk in (0x5B, 0x5C):
                            return 1
                        # Block Alt+Tab
                        if (wParam == WM_SYSKEYDOWN or wParam == WM_KEYDOWN) and vk == 0x09 and alt_pressed:
                            return 1
                        # Block Ctrl+Esc
                        if (wParam == WM_KEYDOWN or wParam == WM_SYSKEYDOWN) and vk == 0x1B and (ctypes.windll.user32.GetKeyState(0x11) & 0x8000):
                            return 1
                except Exception:
                    pass
                return user32.CallNextHookEx(self._hhook, nCode, wParam, lParam)

            self._hook_proc_ptr = LowLevelKeyboardProc(_proc)
            hInstance = kernel32.GetModuleHandleW(None)
            hhook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._hook_proc_ptr, hInstance, 0)
            if hhook == 0:
                return False
            self._hhook = hhook
            self._system_hook_installed = True
            return True
        except Exception:
            return False

    def _uninstall_system_key_block(self):
        if os.name != 'nt':
            return
        try:
            if self._system_hook_installed and self._hhook:
                ctypes.windll.user32.UnhookWindowsHookEx(self._hhook)
        except Exception:
            pass
        finally:
            self._system_hook_installed = False
            self._hhook = None
            self._hook_proc_ptr = None
            # If we grabbed the keyboard at the Qt level, release it now
            try:
                if getattr(self, '_keyboard_grabbed', False):
                    try:
                        self.releaseKeyboard()
                    except Exception:
                        pass
            except Exception:
                pass
            self._keyboard_grabbed = False
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

    def set_template_buttons_enabled(self, enabled: bool):
        """Enable or disable the template quick-access buttons."""
        try:
            for btn, _ in getattr(self, "template_buttons", []):
                btn.setEnabled(enabled)
        except Exception:
            pass

    def remove_template_from_ui(self, template_name):
        """Remove a template from the UI when it produces output."""
        try:
            # Remove from visible_template_keys
            if template_name in self.visible_template_keys:
                self.visible_template_keys.remove(template_name)
            
            # Remove from menu actions
            for i, act in enumerate(self.prog_actions):
                act_text = act.text()
                template_num = int(template_name.replace("prog", ""))
                if f"Prog {template_num}" == act_text:
                    self.prog_actions.pop(i)
                    try:
                        # Remove from menu (we need to find the Programs menu)
                        for menu in self.menu_bar.findChildren(type(self.menu_bar)):
                            if menu.title() == "Programs":
                                menu.removeAction(act)
                                break
                    except Exception:
                        pass
                    break
            
            # Remove from template buttons
            for i, (btn, key) in enumerate(self.template_buttons):
                if key == template_name:
                    btn.deleteLater()  # Remove button from UI
                    self.template_buttons.pop(i)
                    break
            
            # Hide templates panel if no templates remain
            if not self.visible_template_keys:
                self.templates_panel_label.setVisible(False)
                self.templates_panel_widget.setVisible(False)
        except Exception:
            pass

    # (hash-based validation and external-debugger blocking removed)

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
        self.set_template_buttons_enabled(False)
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
            self.output.appendPlainText("❌ERROR DETECTED\n")
            self.output.appendPlainText("Error occurred\n")
            self.runtime_error = True
            self.disable_min_max()
            if self.current_template:
                self.set_error_banner(True, f"❌error detected — Fix the code or switch to another template from the Programs menu")
            else:
                self.set_error_banner(True, "❌error detected — fix code and run to unlock window")
            self.lock_window()
            return

        # (previous code-integrity and external-debugger checks removed)

        self.runtime_error = False
        self.execution_output_produced = False
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

        # Add a runtime guard to the temporary script so it only executes when
        # launched from this IDE process (parent-PID verification).
        guard = (
            "import os,sys\n"
            "_expected_ppid = os.environ.get('MNMJ_PARENT_PID')\n"
            "try:\n"
            "    if _expected_ppid is None or int(_expected_ppid) != os.getppid():\n"
            "        print('❌ Unauthorized execution: script must be run from the MNMJ IDE')\n"
            "        sys.exit(2)\n"
            "except Exception:\n"
            "    print('❌ Unauthorized execution: script must be run from the MNMJ IDE')\n"
            "    sys.exit(2)\n"
            "sys.setrecursionlimit(10**7)\n"
        )
        code = guard + code

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
            # Mark that this run is initiated by the IDE and set a short-lived
            # environment variable the child will check.
            prev_env = os.environ.get('MNMJ_PARENT_PID')
            try:
                os.environ['MNMJ_PARENT_PID'] = str(os.getpid())
                self._last_run_initiated_by_ide = True
                self.process.start(sys.executable, ["-u", self.temp_file])
            finally:
                # restore previous environment variable immediately; child has already inherited it
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
            # install system key block to prevent switching while running
            try:
                if self._install_system_key_block():
                    self._protect_run_active = True
                    # Grab keyboard focus at the Qt level to help prevent app switching
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
            if text.strip():  # Track that we've received actual output
                self.execution_output_produced = True
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
                    self.set_error_banner(True, f"❌ Runtime error detected — Fix the code or switch to another template from the Programs menu.")
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
                        # If output was produced, clear the template
                        if self.execution_output_produced:
                            self.enable_min_max()
                            self.unlock_window()
                            self.set_error_banner(False, "")
                            # Remove the template from UI since it produced output
                            self.remove_template_from_ui(self.current_template)
                            self.current_template = None
                            self.output.appendPlainText(f"\n✅ Template executed successfully with output — template removed and menu minimized. You can now switch to another template from the Programs menu or continue working.")
                        else:
                            # No output produced, unlock normally
                            self.enable_min_max()
                            self.unlock_window()
                            self.set_error_banner(False, "")
                            # After successful run, remove the template as well
                            self.remove_template_from_ui(self.current_template)
                            self.current_template = None
                            self.output.appendPlainText(f"\n✅ Code fixed successfully! Template removed and menu minimized. You can now switch to another template from the Programs menu or continue working.")
                    else:
                        # If the run was not initiated by this IDE, do not unlock.
                        self.disable_min_max()
                        self.lock_window()
                        self.set_error_banner(True, "❌ Template run completed outside IDE permission — window remains locked.")
                    if not (self.group_timer_started and self.group_time_left_ms == 0):
                        self.set_program_actions_enabled(True)
                        self.set_file_actions_enabled(True)
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
            # Activate exam-lock mode after process finishes
            try:
                self.exam_lock_active = True
                self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
                self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
                self.showFullScreen()
                self.output.appendPlainText("\n🔒 EXAM MODE ACTIVE — APP SWITCHING DISABLED")
            except Exception:
                pass
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

    # ⛔ BLOCK CLOSE WHEN IN EXAM MODE
    def closeEvent(self, event):
        if getattr(self, 'exam_lock_active', False):
            QMessageBox.warning(self, "Exam Mode", "Application cannot be closed during exam mode.")
            event.ignore()
        else:
            event.accept()

    # 🔓 ADMIN UNLOCK (Ctrl+F12)
    def keyPressEvent(self, event):
        try:
            if event.key() == Qt.Key_F12 and event.modifiers() == Qt.ControlModifier:
                self.exam_lock_active = False
                try:
                    self._uninstall_system_key_block()
                except Exception:
                    pass
                self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
                self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
                self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
                self.showNormal()
                self.set_error_banner(False, "")
                QMessageBox.information(self, "Unlocked", "Exam mode disabled.")
                return
        except Exception:
            pass
        # fallback to default handler
        super().keyPressEvent(event)

    # ---------- PROGRAM TEMPLATES ----------
    def load_program_template(self, template_name):
        """
        Load any template (from visible or all templates) at any time.
        Run the template code briefly to check for immediate errors.
        Allow switching between templates anytime, even if template has errors.
        """
        if template_name not in self.PROGRAM_TEMPLATES:
            QMessageBox.warning(self, "Error", f"Template '{template_name}' not found.")
            return

        # If group timer expired, block loading
        if self.group_timer_started and self.group_time_left_ms == 0:
            QMessageBox.information(self, "Time Expired", "Template time expired — cannot load templates.")
            return

        # Stop any running process first
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

        # Ask user if they want to discard current content (only if there's unsaved code)
        if self.editor.toPlainText().strip():
            if self.current_template:
                msg = f"Switch to '{template_name}' template? Current template '{self.current_template}' will be discarded (unsaved changes lost)."
            else:
                msg = f"Load '{template_name}' template? This will replace current code."
            resp = QMessageBox.question(
                self, "Load Template", msg,
                QMessageBox.Yes | QMessageBox.No
            )
            if resp != QMessageBox.Yes:
                return

        template_code = self.PROGRAM_TEMPLATES[template_name]

        # --- PRE-RUN: quick, non-interactive execution with timeout ---
        pre_run_result = None
        try:
            # Try compiling first (fast)
            compile(template_code, "<template>", "exec")
            # write to a temporary file for execution
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as tf:
                tf.write(template_code)
                tmp_path = tf.name
            # Run the template briefly with no input; timeout quickly to avoid blocking on input()
            try:
                # 2-second timeout for a quick smoke-run (adjustable)
                completed = subprocess.run([sys.executable, "-u", tmp_path],
                input=None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=2,
                check=False,
                encoding="utf-8")
                # capture minimal info — do NOT show detailed tracebacks to user
                if completed.returncode != 0 or completed.stderr.strip():
                    pre_run_result = "error"
                else:
                    pre_run_result = "ok"
            except subprocess.TimeoutExpired:
                # If the script waits for input or runs longer, we kill it — that's acceptable
                pre_run_result = "timeout"
            except Exception:
                pre_run_result = "error"
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
        except Exception:
            # compilation failed — treat as error but continue to show template
            pre_run_result = "compile_error"

        # Show a small note in output about the pre-run (kept minimal)
        if pre_run_result == "ok":
            self.output.clear()
            self.output.appendPlainText("ℹ️ Template pre-run completed (no immediate errors).\n")
        elif pre_run_result in ("timeout", "error", "compile_error"):
            self.output.clear()
            self.output.appendPlainText("ℹ️ Template pre-run detected an issue (template loaded for fixing).\n")

        # Activate exam mode now (lock the app / disable switching) BEFORE loading template into editor.
        try:
            self.exam_lock_active = True
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
            self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
            try:
                self.showFullScreen()
            except Exception:
                pass
            # Try to install system key block to further reduce switching (best-effort on Windows)
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
            self.output.appendPlainText("\n🔒 EXAM MODE ACTIVE — APP SWITCHING DISABLED\n")
        except Exception:
            pass

        # Now load the template into the editor (as requested: show after pre-run attempt)
        self.editor.setPlainText(template_code)
        self.editor.setReadOnly(False)

        self.current_template = template_name

        # (hash tracking removed for templates)

        # Disable min/max and prevent switching while template is selected
        self.disable_min_max()
        self.set_program_actions_enabled(False)
        self.set_file_actions_enabled(False)

        # Show banner and keep output as-is (pre-run messages remain)
        is_visible = template_name in self.visible_template_keys
        visible_text = "(Visible template)" if is_visible else "(From All Templates)"
        self.set_error_banner(True, f"📝 Template '{template_name}' {visible_text} loaded — Fix the code and run successfully OR switch to another template from the Programs menu")

        # Reset runtime error state and start group timer (if not started) when any template is selected
        self.runtime_error = False
        self.user_input = ""
        self.start_group_timer_if_needed()


    # ---------- FILE OPERATIONS & HELP ----------
    def new_file(self):
        # Prevent creating a new file while a template is active
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
        # template hash tracking removed
        if not (self.group_timer_started and self.group_time_left_ms == 0):
            self.set_program_actions_enabled(True)
            self.set_file_actions_enabled(True)
        self.setWindowTitle("Python Compiler of MNMJEC")
        self.output.clear()
        self.enable_min_max()
        self.set_error_banner(False, "")
        self.runtime_error = False
        self.user_input = ""
        self.exam_lock_active = False

    def open_file(self):
        # Prevent opening another file while a template is active
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
                # template hash tracking removed
                if not (self.group_timer_started and self.group_time_left_ms == 0):
                    self.set_program_actions_enabled(True)
                    self.set_file_actions_enabled(True)
                self.setWindowTitle(f"Python Compiler of MNMJEC - {os.path.basename(path)}")
                self.output.clear()
                self.enable_min_max()
                self.set_error_banner(False, "")
                self.runtime_error = False
                self.user_input = ""
                self.exam_lock_active = False
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
        QMessageBox.information(self, "About", "Offline Python IDE — MNMJEC\nSimple offline code runner.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ide = OfflinePythonIDE()
    ide.show()
    sys.exit(app.exec_())
