import sys
import os
import threading
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                 QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit,
                                 QProgressBar, QFrame, QGridLayout, QSizePolicy, QListWidget,
                                 QListWidgetItem, QDialog)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QPainter, QPixmap, QScreen
from PIL import Image

from core.downloader import VideoDownloader
from core.video_info import fetch_video_info, format_duration
from utils.config import (get_output_dir, set_output_dir, get_proxy, set_proxy,
                          get_default_cookie_file, ensure_app_data_dir)
from utils import check_ffmpeg_available


def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容打包后的exe"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', relative_path)


class FramelessWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(600, 450)

        self.glass = GlassWidget(self)
        self.setCentralWidget(self.glass)

        self.center()

    def center(self):
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - 600) // 2, (screen.height() - 450) // 2)

    def mousePressEvent(self, event):
        if event.position().y() < 35:
            self.dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'dragging') and event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False


class PlaylistDialog(QDialog):
    """播放列表选择对话框（独立弹窗）"""

    selection_changed = Signal(int, int)  # (已选数, 总数)

    def __init__(self, videos, parent=None):
        super().__init__(parent)
        self.videos = videos
        self.setWindowTitle(f'📋 播放列表 - 共 {len(videos)} 个视频')
        self.setMinimumSize(520, 420)
        self.resize(560, 460)
        # 独立窗口 + 任务栏图标
        self.setWindowFlags(self.windowFlags() | Qt.Window)

        self._setup_ui()
        self._populate()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # 标题栏
        title_bar = QHBoxLayout()
        title_lbl = QLabel('📋 选择要下载的视频')
        title_lbl.setFont(QFont('Microsoft YaHei', 11, QFont.Bold))
        title_bar.addWidget(title_lbl)
        title_bar.addStretch()

        self.count_lbl = QLabel('')
        self.count_lbl.setFont(QFont('Microsoft YaHei', 9))
        self.count_lbl.setStyleSheet('color: #5BA3C6;')
        title_bar.addWidget(self.count_lbl)
        layout.addLayout(title_bar)

        # 视频列表
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont('Microsoft YaHei', 9))
        self.list_widget.setSelectionMode(QListWidget.NoSelection)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #FFFFFF;
                border: 1px solid #87CEEB;
                border-radius: 8px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-radius: 4px;
                border-bottom: 1px solid #F0F0F0;
            }
            QListWidget::item:hover {
                background-color: rgba(135, 206, 235, 60);
            }
            QListWidget::item:checked {
                background-color: rgba(135, 206, 235, 200);
                color: #003366;
            }
        """)
        self.list_widget.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.list_widget, 1)

        # 按钮区
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(8)

        self.btn_all = QPushButton('☑️ 全选')
        self.btn_all.setFont(QFont('Microsoft YaHei', 9, QFont.Bold))
        self.btn_all.setFixedSize(90, 32)
        self.btn_all.setCursor(Qt.PointingHandCursor)
        self.btn_all.setStyleSheet("""
            QPushButton {
                background-color: #FF69B4; color: white;
                border-radius: 16px; border: none;
            }
            QPushButton:hover { background-color: #FF1493; }
        """)
        self.btn_all.clicked.connect(self._on_toggle_all)
        btn_bar.addWidget(self.btn_all)

        self.btn_invert = QPushButton('🔄 反选')
        self.btn_invert.setFont(QFont('Microsoft YaHei', 9, QFont.Bold))
        self.btn_invert.setFixedSize(90, 32)
        self.btn_invert.setCursor(Qt.PointingHandCursor)
        self.btn_invert.setStyleSheet("""
            QPushButton {
                background-color: #87CEEB; color: white;
                border-radius: 16px; border: none;
            }
            QPushButton:hover { background-color: #5BA3C6; }
        """)
        self.btn_invert.clicked.connect(self._on_invert)
        btn_bar.addWidget(self.btn_invert)

        btn_bar.addStretch()

        self.btn_close = QPushButton('✅ 确定')
        self.btn_close.setFont(QFont('Microsoft YaHei', 9, QFont.Bold))
        self.btn_close.setFixedSize(100, 32)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #32CD32; color: white;
                border-radius: 16px; border: none;
            }
            QPushButton:hover { background-color: #228B22; }
        """)
        self.btn_close.clicked.connect(self.accept)
        btn_bar.addWidget(self.btn_close)
        layout.addLayout(btn_bar)

    def _populate(self):
        """填充视频列表（默认全选）"""
        self.list_widget.blockSignals(True)
        for v in self.videos:
            item = QListWidgetItem(f"{v['index']:02d}. {v['title']}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, v['index'] - 1)
            # 灰色显示时长
            duration = v.get('duration') or 0
            if duration:
                m, s = divmod(int(duration), 60)
                h, m = divmod(m, 60)
                dur_str = f"{h:02d}:{m:02d}:{s:02d}"
                item.setText(f"{v['index']:02d}. {v['title']}  ({dur_str})")
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)
        self._update_count()

    def _update_count(self):
        total = len(self.videos)
        sel = sum(1 for i in range(self.list_widget.count())
                  if self.list_widget.item(i).checkState() == Qt.Checked)
        self.count_lbl.setText(f'已选 {sel}/{total}')
        self.btn_all.setText('❌ 全不选' if sel == total else '☑️ 全选')
        self.selection_changed.emit(sel, total)

    def _on_item_changed(self, item):
        self._update_count()

    def _on_toggle_all(self):
        total = self.list_widget.count()
        all_selected = all(
            self.list_widget.item(i).checkState() == Qt.Checked
            for i in range(total)
        )
        self.list_widget.blockSignals(True)
        state = Qt.Unchecked if all_selected else Qt.Checked
        for i in range(total):
            self.list_widget.item(i).setCheckState(state)
        self.list_widget.blockSignals(False)
        self._update_count()

    def _on_invert(self):
        total = self.list_widget.count()
        self.list_widget.blockSignals(True)
        for i in range(total):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)
        self.list_widget.blockSignals(False)
        self._update_count()

    def get_selected_indices(self) -> list:
        """返回选中的视频索引列表（0-based）"""
        result = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                result.append(item.data(Qt.UserRole))
        return result


class GlassWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        bg_path = resource_path('小猫_600x450.jpg')
        self.bg_pixmap = None

        if os.path.exists(bg_path):
            try:
                image = Image.open(bg_path)
                image = image.resize((600, 450), Image.Resampling.LANCZOS)
                image.save('temp_bg.png')
                self.bg_pixmap = QPixmap('temp_bg.png')
                os.remove('temp_bg.png')
            except:
                pass

        self.downloader = None
        self.output_dir = get_output_dir()
        self.proxy = get_proxy()
        self.video_info = None
        self.is_downloading = False
        self.playlist_videos = []  # 播放列表视频列表
        self.selected_videos = set()  # 选中的视频索引

        self._setup_ui()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.bg_pixmap:
            painter.drawPixmap(0, 0, self.bg_pixmap)

    def _btn(self, text, color='#87CEEB', icon=''):
        b = QPushButton(f'{icon} {text}' if icon else text)
        b.setFont(QFont('Microsoft YaHei', 9, QFont.Bold))
        b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 15px;
                padding: 6px 14px;
                border: none;
            }}
            QPushButton:hover {{ opacity: 0.85; }}
            QPushButton:disabled {{ background-color: #CCCCCC; }}
        """)
        return b

    def _input(self, placeholder=''):
        e = QLineEdit()
        e.setPlaceholderText(placeholder)
        e.setFont(QFont('Microsoft YaHei', 9))
        e.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 150);
                border: 2px solid #87CEEB;
                border-radius: 15px;
                padding: 5px 12px;
                color: #333;
                selection-background-color: #87CEEB;
            }
            QLineEdit:focus { border-color: #5BA3C6; background-color: rgba(255, 255, 255, 200); }
        """)
        return e

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(15, 10, 15, 8)
        main.setSpacing(4)

        # ===== 标题栏 =====
        title = QFrame()
        title.setStyleSheet('QFrame { background-color: rgba(255,255,255,55); border-radius: 8px; border: none; }')
        tl = QHBoxLayout(title)
        tl.setContentsMargins(12, 3, 12, 3)

        lbl = QLabel('🐱 YouTube & B站下载器')
        lbl.setFont(QFont('Microsoft YaHei', 11, QFont.Bold))
        lbl.setStyleSheet('color: black; background: transparent; border: none;')

        min_b = QPushButton('─')
        min_b.setFixedSize(20, 20)
        min_b.setFont(QFont('Arial', 10))
        min_b.setStyleSheet('background-color: #87CEEB; color: white; border-radius: 10px; border: none;')
        min_b.clicked.connect(lambda: self.window().showMinimized())

        close_b = QPushButton('✕')
        close_b.setFixedSize(20, 20)
        close_b.setFont(QFont('Arial', 9))
        close_b.setStyleSheet('background-color: #DC143C; color: white; border-radius: 10px; border: none;')
        close_b.clicked.connect(lambda: self.window().close())

        tl.addWidget(lbl)
        tl.addStretch()
        tl.addWidget(min_b)
        tl.addWidget(close_b)
        main.addWidget(title)

        # ===== URL输入区 (2/3宽度居中) =====
        url_lbl = QLabel('📎 视频链接')
        url_lbl.setFont(QFont('Microsoft YaHei', 8, QFont.Bold))
        main.addWidget(url_lbl, alignment=Qt.AlignCenter)

        url_row_w = QWidget()
        url_row = QHBoxLayout(url_row_w)
        url_row.setContentsMargins(0, 0, 0, 0)
        url_row.addStretch()

        inner_url = QWidget()
        inner_url.setFixedWidth(500)
        inner_url_layout = QHBoxLayout(inner_url)
        inner_url_layout.setContentsMargins(0, 0, 0, 0)

        self.url_input = self._input('粘贴视频链接...')
        self.url_input.setMinimumHeight(26)
        self.url_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.fetch_btn = self._btn('获取', '#87CEEB', '🔍')
        self.fetch_btn.setFixedWidth(80)
        self.fetch_btn.clicked.connect(self._on_fetch)

        inner_url_layout.addWidget(self.url_input, 1)
        inner_url_layout.addWidget(self.fetch_btn)
        url_row.addWidget(inner_url)
        url_row.addStretch()
        main.addWidget(url_row_w)

        # ===== 视频信息区 (2/3宽度居中) =====
        info_w = QWidget()
        info_layout_outer = QHBoxLayout(info_w)
        info_layout_outer.setContentsMargins(0, 0, 0, 0)
        info_layout_outer.addStretch()

        info_inner = QWidget()
        info_inner.setFixedWidth(500)
        info_inner.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 55);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 60);
            }
        """)
        gl = QGridLayout(info_inner)
        gl.setContentsMargins(8, 5, 8, 5)
        gl.setSpacing(3)

        gl.addWidget(QLabel('📺'), 0, 0)
        self.title_lbl = QLabel('-')
        self.title_lbl.setFont(QFont('Microsoft YaHei', 7))
        self.title_lbl.setStyleSheet('color: #5BA3C6; background: transparent; border: none;')
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        gl.addWidget(self.title_lbl, 0, 1, 1, 2)

        gl.addWidget(QLabel('⏱️'), 1, 0)
        self.duration_lbl = QLabel('--:--:--')
        self.duration_lbl.setFont(QFont('Microsoft YaHei', 7))
        self.duration_lbl.setStyleSheet('background: transparent; border: none;')
        gl.addWidget(self.duration_lbl, 1, 1)

        gl.addWidget(QLabel('📐'), 1, 2)
        self.format_combo = QComboBox()
        self.format_combo.addItem('先获取视频')
        self.format_combo.setEnabled(False)
        self.format_combo.setFont(QFont('Microsoft YaHei', 7))
        self.format_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid #87CEEB;
                border-radius: 8px;
                padding: 2px 6px;
            }
        """)
        gl.addWidget(self.format_combo, 1, 3)

        self.playlist_chk = QPushButton('📋 播放列表')
        self.playlist_chk.setFont(QFont('Microsoft YaHei', 7))
        # 改为普通按钮：点击弹出独立弹窗，不再嵌在主窗口里
        self.playlist_chk.setCheckable(False)
        self.playlist_chk.setEnabled(False)
        self.playlist_chk.setCursor(Qt.PointingHandCursor)
        self.playlist_chk.setStyleSheet("""
            QPushButton {
                background-color: rgba(200, 200, 200, 150);
                color: #666;
                border-radius: 10px;
                padding: 4px 8px;
                border: none;
            }
            QPushButton:hover { background-color: rgba(135, 206, 235, 200); color: #333; }
        """)
        self.playlist_chk.clicked.connect(self._on_open_playlist_dialog)
        gl.addWidget(self.playlist_chk, 1, 4)

        # ===== 播放列表区域 (2/3宽度居中，可折叠) =====
        # 改为弹窗方案：保留 widget 占位（兼容旧代码引用），但默认隐藏、实际不用
        self.playlist_w = QWidget()
        self.playlist_w.setVisible(False)
        self.playlist_w.setFixedHeight(0)
        self.playlist_w.setStyleSheet('background: transparent;')
        pl_layout_outer = QHBoxLayout(self.playlist_w)
        pl_layout_outer.setContentsMargins(0, 0, 0, 0)
        pl_layout_outer.addStretch()

        pl_inner = QWidget()
        pl_inner.setFixedWidth(560)
        pl_inner.setStyleSheet("background-color: transparent;")
        pl_vl = QVBoxLayout(pl_inner)
        pl_vl.setContentsMargins(8, 4, 8, 4)
        pl_vl.setSpacing(4)

        pl_hl = QHBoxLayout()
        pl_hl.setSpacing(8)
        lbl_pl = QLabel('📋 播放列表')
        lbl_pl.setFont(QFont('Microsoft YaHei', 9, QFont.Bold))
        lbl_pl.setStyleSheet('color: #333;')
        pl_hl.addWidget(lbl_pl)

        self.pl_all_btn = QPushButton('☑️ 全选')
        self.pl_all_btn.setFont(QFont('Microsoft YaHei', 8, QFont.Bold))
        self.pl_all_btn.setFixedSize(70, 24)
        self.pl_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF69B4;
                color: white;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background-color: #FF1493; }
        """)
        # pl_all_btn 在隐藏的占位 widget 里，逻辑已迁到 PlaylistDialog
        # 这里 connect 一个 noop，避免 AttributeError
        self.pl_all_btn.clicked.connect(lambda: None)
        pl_hl.addWidget(self.pl_all_btn)

        self.pl_invert_btn = QPushButton('🔄 反选')
        self.pl_invert_btn.setFont(QFont('Microsoft YaHei', 8, QFont.Bold))
        self.pl_invert_btn.setFixedSize(70, 24)
        self.pl_invert_btn.setStyleSheet("""
            QPushButton {
                background-color: #87CEEB;
                color: white;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background-color: #5BA3C6; }
        """)
        # pl_invert_btn 在隐藏的占位 widget 里，逻辑已迁到 PlaylistDialog
        self.pl_invert_btn.clicked.connect(lambda: None)
        pl_hl.addWidget(self.pl_invert_btn)

        pl_hl.addStretch()

        self.pl_count_lbl = QLabel('共0个')
        self.pl_count_lbl.setFont(QFont('Microsoft YaHei', 8))
        self.pl_count_lbl.setStyleSheet('color: #333; background: transparent;')
        pl_hl.addWidget(self.pl_count_lbl)

        pl_vl.addLayout(pl_hl)

        self.pl_list = QListWidget()
        self.pl_list.setFont(QFont('Microsoft YaHei', 8))
        self.pl_list.setSelectionMode(QListWidget.NoSelection)
        # 关键修复：限制列表本身最大高度，超出滚动显示
        self.pl_list.setMaximumHeight(130)
        # 保证垂直方向有滚动条
        self.pl_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.pl_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.pl_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid #87CEEB;
                border-radius: 6px;
                padding: 2px;
            }
            QListWidget::item {
                padding: 3px 6px;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background-color: rgba(135, 206, 235, 80);
            }
            QListWidget::item:checked {
                background-color: rgba(135, 206, 235, 180);
                color: #003366;
            }
        """)
        self.pl_list.itemChanged.connect(self._on_playlist_item_changed_legacy)
        pl_vl.addWidget(self.pl_list)

        pl_layout_outer.addWidget(pl_inner)
        pl_layout_outer.addStretch()

        
        info_layout_outer.addWidget(info_inner)
        info_layout_outer.addStretch()
        main.addWidget(info_w)

        # 播放列表区域（保留占位但不显示，实际使用弹窗）
        main.addWidget(self.playlist_w)

        # ===== 路径和代理区 (2/3宽度居中) =====
        path_w = QWidget()
        path_row = QHBoxLayout(path_w)
        path_row.setContentsMargins(0, 0, 0, 0)
        path_row.addStretch()

        path_lbl = QLabel('下载目录:')
        path_lbl.setFont(QFont('Microsoft YaHei', 9))
        path_lbl.setStyleSheet('background: transparent; color: #FFD700;')
        path_lbl.setFixedWidth(65)

        path_inner = QWidget()
        path_inner.setFixedWidth(440)
        pl = QHBoxLayout(path_inner)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(6)

        self.path_input = self._input()
        self.path_input.setText(self.output_dir)
        self.path_input.setMinimumHeight(24)
        self.path_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.browse_btn = self._btn('浏览', '#87CEEB', '📂')
        self.browse_btn.setFixedWidth(80)
        self.browse_btn.clicked.connect(self._on_browse)

        pl.addWidget(self.path_input, 1)
        pl.addWidget(self.browse_btn)
        path_row.addWidget(path_lbl)
        path_row.addWidget(path_inner)
        path_row.addStretch()
        main.addWidget(path_w)

        proxy_w = QWidget()
        proxy_row = QHBoxLayout(proxy_w)
        proxy_row.setContentsMargins(0, 0, 0, 0)
        proxy_row.addStretch()

        proxy_lbl = QLabel('代理地址:')
        proxy_lbl.setFont(QFont('Microsoft YaHei', 9))
        proxy_lbl.setStyleSheet('background: transparent; color: #FFD700;')
        proxy_lbl.setFixedWidth(65)

        proxy_inner = QWidget()
        proxy_inner.setFixedWidth(440)
        prl = QHBoxLayout(proxy_inner)
        prl.setContentsMargins(0, 0, 0, 0)
        prl.setSpacing(6)

        self.proxy_input = self._input('http://127.0.0.1:10808')
        self.proxy_input.setText(self.proxy)
        self.proxy_input.setMinimumHeight(24)
        self.proxy_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.save_proxy_btn = self._btn('保存', '#87CEEB', '💾')
        self.save_proxy_btn.setFixedWidth(80)
        self.save_proxy_btn.clicked.connect(self._on_save_proxy)

        prl.addWidget(self.proxy_input, 1)
        prl.addWidget(self.save_proxy_btn)
        proxy_row.addWidget(proxy_lbl)
        proxy_row.addWidget(proxy_inner)
        proxy_row.addStretch()
        main.addWidget(proxy_w)

        # ===== Cookie文件 =====
        cookie_w = QWidget()
        main.addWidget(cookie_w)
        cookie_layout = QHBoxLayout(cookie_w)
        cookie_layout.setContentsMargins(0, 0, 0, 0)
        cookie_layout.addStretch()

        cookie_lbl = QLabel('Cookie:')
        cookie_lbl.setFont(QFont('Microsoft YaHei', 9))
        cookie_lbl.setStyleSheet('background: transparent; color: #FFD700;')
        cookie_lbl.setFixedWidth(65)

        cookie_inner = QWidget()
        cookie_inner.setFixedWidth(440)
        cookie_inner.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 60);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 60);
            }
        """)
        cl = QHBoxLayout(cookie_inner)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(6)

        self.cookie_input = self._input('')
        self.cookie_input.setMinimumHeight(24)
        self.cookie_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cookie_input.setPlaceholderText('Cookie文件路径')
        cookie_default = get_default_cookie_file()
        ensure_app_data_dir()  # 确保用户数据目录存在
        if os.path.exists(cookie_default):
            self.cookie_input.setText(cookie_default)
        self.browse_cookie_btn = self._btn('浏览', '#87CEEB', '📁')
        self.browse_cookie_btn.setFixedWidth(80)
        self.browse_cookie_btn.clicked.connect(self._on_browse_cookie)

        cl.addWidget(self.cookie_input, 1)
        cl.addWidget(self.browse_cookie_btn)
        cookie_layout.addWidget(cookie_lbl)
        cookie_layout.addWidget(cookie_inner)
        cookie_layout.addStretch()

        # ===== 进度区 (2/3宽度居中) =====
        prog_w = QWidget()
        prog_layout = QHBoxLayout(prog_w)
        prog_layout.setContentsMargins(0, 0, 0, 0)
        prog_layout.addStretch()

        prog_inner = QWidget()
        prog_inner.setFixedWidth(500)
        prog_inner.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 60);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 60);
            }
        """)
        prog_vl = QVBoxLayout(prog_inner)
        prog_vl.setContentsMargins(8, 4, 8, 4)
        prog_vl.setSpacing(2)

        self.progress_lbl = QLabel('0%')
        self.progress_lbl.setFont(QFont('Microsoft YaHei', 7))
        self.progress_lbl.setStyleSheet('background: transparent; border: none;')
        prog_vl.addWidget(self.progress_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #E0E0E0;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #87CEEB, stop:1 #5BA3C6);
                border-radius: 4px;
            }
        """)
        prog_vl.addWidget(self.progress_bar)

        self.speed_lbl = QLabel('')
        self.speed_lbl.setFont(QFont('Microsoft YaHei', 6))
        self.speed_lbl.setStyleSheet('color: #666; background: transparent; border: none;')
        prog_vl.addWidget(self.speed_lbl)

        prog_layout.addWidget(prog_inner)
        prog_layout.addStretch()
        main.addWidget(prog_w)

        # ===== 日志+下载按钮区 (2/3宽度居中) =====
        bottom_w = QWidget()
        bottom = QHBoxLayout(bottom_w)
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.addStretch()

        bottom_inner = QWidget()
        bottom_inner.setFixedWidth(480)
        bl = QHBoxLayout(bottom_inner)
        bl.setSpacing(10)

        # 日志区
        log = QWidget()
        log.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 50);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 60);
            }
        """)
        log_layout = QVBoxLayout(log)
        log_layout.setContentsMargins(6, 4, 6, 4)
        log_layout.setSpacing(1)
        log_title = QLabel('📜 下载日志')
        log_title.setFont(QFont('Microsoft YaHei', 7, QFont.Bold))
        log_title.setStyleSheet('background: transparent; border: none;')
        log_layout.addWidget(log_title)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont('Consolas', 6))
        self.log_text.setStyleSheet('background-color: rgba(255, 255, 255, 180); border-radius: 6px; border: none; padding: 3px;')
        self.log_text.setMinimumHeight(50)
        log_layout.addWidget(self.log_text)

        self.status_lbl = QLabel('🐾 就绪' if check_ffmpeg_available() else '⚠️ 未检测到ffmpeg，下载无声')
        self.status_lbl.setFont(QFont('Microsoft YaHei', 7))
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet('background-color: rgba(255,182,193,150); border-radius: 5px; padding: 2px 6px;')
        log_layout.addWidget(self.status_lbl)

        # 下载按钮
        dl_container = QWidget()
        dl_layout = QVBoxLayout(dl_container)
        dl_layout.setContentsMargins(0, 0, 0, 0)
        dl_layout.addStretch()

        self.download_btn = QPushButton('🐾 开始下载 🐾')
        self.download_btn.setFont(QFont('Microsoft YaHei', 8, QFont.Bold))
        self.download_btn.setEnabled(False)
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFB6C1, stop:1 #FF69B4);
                color: white;
                border-radius: 14px;
                padding: 6px 14px;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover { opacity: 0.85; }
            QPushButton:disabled { background-color: #CCCCCC; }
        """)
        self.download_btn.clicked.connect(self._on_download)
        dl_layout.addWidget(self.download_btn)
        dl_layout.addStretch()

        bl.addWidget(log, 65)
        bl.addWidget(dl_container, 35)
        bottom.addWidget(bottom_inner)
        bottom.addStretch()
        main.addWidget(bottom_w)

    def _log(self, msg):
        if msg:
            self.log_text.append(msg)

    def _on_fetch(self):
        url = self.url_input.text().strip()
        if not url:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, '提示', '请输入视频链接')
            return

        self.fetch_btn.setEnabled(False)
        self.status_lbl.setText('🔄 获取中...')
        self._log(f'获取: {url}')

        class FT(QThread):
            done = Signal(dict)
            err = Signal(str)

            def __init__(self, u, p, c):
                super().__init__()
                self.u, self.p, self.c = u, p, c

            def run(self):
                try:
                    info = fetch_video_info(self.u, proxy=self.p if self.p else None, cookie_file=self.c if self.c else None)
                    self.done.emit(info)
                except Exception as e:
                    self.err.emit(str(e))

        cookie_path = self.cookie_input.text().strip()
        self._ft = FT(url, self.proxy_input.text().strip(), cookie_path)
        self._ft.done.connect(self._on_fetch_done)
        self._ft.err.connect(self._on_fetch_err)
        self._ft.start()

    @Slot(dict)
    def _on_fetch_done(self, info):
        self.video_info = info
        self.title_lbl.setText(info['title'][:30] + ('...' if len(info['title']) > 30 else ''))
        self.duration_lbl.setText(format_duration(info['duration']))

        ress = []
        seen = set()
        for f in info['formats']:
            r = f['resolution']
            # 只提取纯分辨率如 "1080p", "720p"
            import re
            match = re.match(r'^(\d+)p', r, re.IGNORECASE)
            if match:
                r_clean = match.group(1) + 'p'
                if r_clean not in seen:
                    seen.add(r_clean)
                    ress.append(r_clean)
        ress = sorted(ress, key=lambda x: int(x.rstrip('p')) if x.rstrip('p').isdigit() else 0, reverse=True)

        self.format_combo.clear()
        self.format_combo.addItems(ress if ress else ['best'])
        self.format_combo.setEnabled(True)
        self.download_btn.setEnabled(True)
        self.fetch_btn.setEnabled(True)

        # 检测是否为播放列表
        self._log(f'[DBG] is_playlist={info.get("is_playlist")}, playlist_count={info.get("playlist_count", 0)}')
        if info.get('is_playlist'):
            self.playlist_chk.setEnabled(True)
            pc = info.get('playlist_count', 0)
            self.status_lbl.setText(f'📋 播放列表 ({pc}个视频)')
            self._log(f'📋 播放列表: {pc}个视频')
            # 显示播放列表
            self._load_playlist_videos(info)
        else:
            self.playlist_chk.setEnabled(False)
            self.playlist_w.setVisible(False)
            self.status_lbl.setText(f'🐾 可选: {", ".join(ress[:3])}')
        self._log(f'✅ 成功!')

    def _load_playlist_videos(self, info):
        """加载播放列表视频"""
        from core.video_info import fetch_playlist_info

        url = self.url_input.text().strip()
        proxy = self.proxy_input.text().strip()
        cookie_path = self.cookie_input.text().strip()

        class PLT(QThread):
            done = Signal(list)
            err = Signal(str)

            def __init__(self, u, p, c):
                super().__init__()
                self.u, self.p, self.c = u, p, c

            def run(self):
                try:
                    videos = fetch_playlist_info(self.u, proxy=self.p if self.p else None, cookie_file=self.c if self.c else None)
                    self.done.emit(videos)
                except Exception as e:
                    self.err.emit(str(e))

        self._plt = PLT(url, proxy, cookie_path)
        self._plt.done.connect(self._on_playlist_loaded)
        self._plt.err.connect(self._on_playlist_load_err)
        self._plt.start()

    @Slot(list)
    def _on_playlist_loaded(self, videos):
        self._log(f'[DBG] _on_playlist_loaded 收到 {len(videos)} 个视频')
        if not videos:
            self._log('⚠️ 播放列表为空')
            return
        self.playlist_videos = videos
        self.selected_videos = set(range(len(videos)))  # 默认全选

        # 启用"播放列表"按钮
        self.playlist_chk.setEnabled(True)
        self.playlist_chk.setText(f'📋 播放列表 ({len(videos)})')
        self.download_btn.setEnabled(True)

        # 自动弹出独立窗口
        self._open_playlist_dialog()

        self._log(f'✅ 已加载 {len(videos)} 个视频，已弹出选择窗口')

    def _open_playlist_dialog(self):
        """打开播放列表选择弹窗（独立窗口）"""
        if not self.playlist_videos:
            return
        # 如果已存在且未关闭，复用并置顶
        if hasattr(self, '_playlist_dialog') and self._playlist_dialog is not None:
            try:
                self._playlist_dialog.show()
                self._playlist_dialog.raise_()
                self._playlist_dialog.activateWindow()
                return
            except RuntimeError:
                self._playlist_dialog = None

        self._playlist_dialog = PlaylistDialog(self.playlist_videos, self)
        self._playlist_dialog.selection_changed.connect(self._on_dialog_selection_changed)
        # 居中显示在主窗口旁边
        self._position_dialog_near_main()
        self._playlist_dialog.show()

    def _position_dialog_near_main(self):
        """把弹窗放在主窗口右侧（屏幕装不下时回退居中）"""
        if not hasattr(self, '_playlist_dialog') or not self._playlist_dialog:
            return
        screen = QApplication.primaryScreen().geometry()
        main_rect = self.geometry()
        dlg_w, dlg_h = self._playlist_dialog.width(), self._playlist_dialog.height()
        # 尝试放在主窗口右侧
        x = main_rect.right() + 10
        y = main_rect.top()
        # 右侧装不下就放左侧
        if x + dlg_w > screen.right():
            x = main_rect.left() - dlg_w - 10
        # 左侧也装不下就居中
        if x < screen.left():
            x = (screen.width() - dlg_w) // 2
            y = (screen.height() - dlg_h) // 2
        self._playlist_dialog.move(x, y)

    def _on_open_playlist_dialog(self):
        """用户点击主窗口的"播放列表"按钮时调用"""
        if not self.playlist_videos:
            self._log('⚠️ 请先点击"获取"加载播放列表')
            return
        self._open_playlist_dialog()

    def _on_dialog_selection_changed(self, sel, total):
        """弹窗里选中数变化时同步到主窗口"""
        self.selected_videos = set()
        if hasattr(self, '_playlist_dialog') and self._playlist_dialog:
            for idx in self._playlist_dialog.get_selected_indices():
                self.selected_videos.add(idx)
        # 更新主窗口按钮文字
        if self.playlist_videos:
            self.playlist_chk.setText(f'📋 播放列表 ({len(self.selected_videos)}/{len(self.playlist_videos)})')

    # 注：_on_playlist_item_changed / _on_playlist_invert / _on_playlist_select_all
    # 这些方法已废弃，相关逻辑移到了 PlaylistDialog 类里。
    # 主窗口通过 _on_dialog_selection_changed 接收选择变化。

    def _on_playlist_item_changed_legacy(self, item):
        """旧 pl_list（已隐藏）的占位回调，不再更新 UI（弹窗是主交互入口）"""
        pass

    @Slot(str)
    def _on_playlist_load_err(self, e):
        from PySide6.QtWidgets import QMessageBox
        self._log(f'❌ 加载播放列表失败: {e}')
        QMessageBox.critical(self, '加载播放列表失败', f'{e}\n\n可能原因：\n1. Cookie 文件无效或已过期，请重新导出\n2. 网络问题或需要代理\n3. 链接不是有效的播放列表')
        self.playlist_w.setVisible(False)
        self.playlist_chk.setEnabled(False)
        self.fetch_btn.setEnabled(True)
        self.status_lbl.setText('❌ 加载失败')

    @Slot(str)
    def _on_fetch_err(self, e):
        from PySide6.QtWidgets import QMessageBox
        # 去掉 ANSI 颜色码（如 [0;31m、[0m）
        import re
        clean = re.sub(r'\x1b\[[0-9;]*m', '', e)
        QMessageBox.critical(self, '错误', f'获取失败:\n{clean}')
        self.fetch_btn.setEnabled(True)
        self.status_lbl.setText('🐾 就绪')

    def _on_browse(self):
        from PySide6.QtWidgets import QFileDialog
        d = QFileDialog.getExistingDirectory(self, '选择路径', self.output_dir)
        if d:
            self.output_dir = d
            self.path_input.setText(d)
            set_output_dir(d)

    def _on_browse_cookie(self):
        from PySide6.QtWidgets import QFileDialog
        f, _ = QFileDialog.getOpenFileName(self, '选择Cookie文件', '', 'Cookie Files (*.txt);;All Files (*)')
        if f:
            self.cookie_input.setText(f)
            self._log(f'🍪 Cookie文件已选择: {f}')

    def _on_save_proxy(self):
        p = self.proxy_input.text().strip()
        set_proxy(p)
        self._log(f'💾 代理已保存')

    def _on_download(self):
        if self.is_downloading:
            if hasattr(self, '_cancel_event') and self._cancel_event:
                self._cancel_event.set()
            self.status_lbl.setText('⏹ 已取消')
            self._log('取消下载')
            self.is_downloading = False
            self._reset_download_btn()
            return

        url = self.url_input.text().strip()
        if not url or not self.video_info:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, '提示', '请先获取视频')
            return

        fmt = self.format_combo.currentText()
        is_playlist = self.playlist_chk.isChecked() and self.playlist_chk.isEnabled()
        selected_items = sorted([v + 1 for v in self.selected_videos]) if self.selected_videos else None

        self.download_btn.setText('⏹ 取消')
        self.download_btn.setStyleSheet('background-color: #DC143C; color: white; border-radius: 14px; padding: 6px 14px; border: none;')
        self.is_downloading = True
        self.progress_bar.setValue(0)
        self.progress_lbl.setText('0%')
        self.speed_lbl.setText('')
        self.status_lbl.setText(f'🔄 {"播放列表" if is_playlist else ""}下载中...')
        self._log(f'开始下载: {fmt}')

        os.makedirs(self.output_dir, exist_ok=True)
        cookie_path = self.cookie_input.text().strip()
        self.downloader = VideoDownloader(self.output_dir, proxy=self.proxy_input.text().strip() or None, cookie_file=cookie_path if cookie_path else None)

        # 创建取消事件并存储在GlassWidget实例上
        self._cancel_event = threading.Event()

        class DT(QThread):
            prog = Signal(dict)
            done = Signal()
            err = Signal(str)

            def __init__(self, dl, u, f, is_pl, pl_items, cancel_ev):
                super().__init__()
                self.dl, self.u, self.f = dl, u, f
                self.is_pl = is_pl
                self.pl_items = pl_items
                self.cancel_ev = cancel_ev

            def run(self):
                try:
                    def h(d):
                        # 直接传递所有进度数据
                        self.prog.emit(d)

                    if self.is_pl:
                        result = self.dl.download_playlist(self.u, self.f, progress_callback=h, cancel_event=self.cancel_ev, playlist_items=self.pl_items)
                        # 把播放列表下载结果暂存到 GlassWidget，供 _on_done 读取
                        # result = {'titles': [...], 'skipped': [...]}
                        try:
                            QApplication.instance()._last_playlist_result = result
                        except Exception:
                            pass
                    else:
                        title = self.dl.download(self.u, self.f, progress_callback=h, cancel_event=self.cancel_ev)
                        # 单视频下载：title 为 None 表示失败
                        try:
                            app = QApplication.instance()
                            app._last_single_title = title
                            app._last_single_title_set = True
                        except Exception:
                            pass
                    self.done.emit()
                except Exception as e:
                    self.err.emit(str(e))

        self._dt = DT(self.downloader, url, fmt, is_playlist, selected_items, self._cancel_event)
        self._dt.prog.connect(self._on_prog)
        self._dt.done.connect(self._on_done)
        self._dt.err.connect(self._on_err)
        self._dt.start()
        self._log(f'⬇️ {"播放列表" if is_playlist else ""}下载 ({fmt})')

    @Slot(dict)
    def _on_prog(self, d):
        info = d.get('info', '')
        pct = d.get('pct', 0)

        if pct > 0:
            self.progress_bar.setValue(int(pct))
            self.progress_lbl.setText(f'{pct:.1f}%')
        elif info:
            # 过滤掉不需要的日志行
            skip_keywords = ['目的地', 'Destination', 'Deleting original', 'Merging', 'C:\\']
            if not any(kw in info for kw in skip_keywords):
                self._log(info[:80])

    @Slot()
    def _on_done(self):
        self.is_downloading = False
        self._reset_download_btn()
        self.progress_bar.setValue(100)

        # 显示下载结果统计
        app = QApplication.instance()
        # 播放列表
        pl_result = getattr(app, '_last_playlist_result', None)
        if pl_result is not None:
            titles = pl_result.get('titles', [])
            skipped = pl_result.get('skipped', [])
            self._log(f'✅ 播放列表下载完成: 成功 {len(titles)} 个')
            if skipped:
                self._log(f'⏭ 跳过 {len(skipped)} 个失败视频')
                for s in skipped[:5]:
                    self._log(f'   - {s[:60]}')
                if len(skipped) > 5:
                    self._log(f'   ... 还有 {len(skipped)-5} 个')
                self.status_lbl.setText(f'✅ 完成 ({len(titles)} 成功, {len(skipped)} 跳过)')
            else:
                self.status_lbl.setText(f'✅ 全部完成 ({len(titles)} 个)')
            app._last_playlist_result = None
        else:
            # 单视频
            single_title = getattr(app, '_last_single_title', None)
            if single_title is None and getattr(app, '_last_single_title_set', False):
                self._log('❌ 视频下载失败（可能已删除/地区限制/无权限）')
                self.status_lbl.setText('⚠️ 下载失败')
            else:
                self._log(f'✅ 下载完成: {single_title}')
                self.status_lbl.setText('✅ 完成!')
            app._last_single_title = None
            app._last_single_title_set = False

    @Slot(str)
    def _on_err(self, e):
        if 'cancelled' in str(e).lower():
            self.status_lbl.setText('⏹ 已取消')
            self._log('下载已取消')
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, '错误', f'下载失败:\n{e}')
            self.status_lbl.setText('❌ 失败')
            self._log(f'❌ {e}')
        self.is_downloading = False
        self._reset_download_btn()

    def _reset_download_btn(self):
        self.download_btn.setText('🐾 开始下载 🐾')
        self.download_btn.setStyleSheet('background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFB6C1, stop:1 #FF69B4); color: white; border-radius: 18px; padding: 8px 20px; border: none;')


def create_gui():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    w = FramelessWindow()
    w.show()
    sys.exit(app.exec())
