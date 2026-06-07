import os
import shutil
import subprocess
from urllib.parse import urlparse


def get_referer(url: str) -> str:
    """从 URL 提取域名作为 Referer"""
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return 'https://www.youtube.com'


def find_ffmpeg() -> str | None:
    """查找 ffmpeg 可执行文件路径，找不到返回 None"""
    # 先检查 PATH
    path = shutil.which('ffmpeg')
    if path:
        return path
    # PyInstaller 打包后的路径
    import sys
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
        local_ffmpeg = os.path.join(base, 'bin', 'ffmpeg.exe')
        if os.path.exists(local_ffmpeg):
            return local_ffmpeg
    # 开发环境的项目 bin 目录
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_ffmpeg = os.path.join(project_dir, 'bin', 'ffmpeg.exe')
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
    return None


def check_ffmpeg_available() -> bool:
    """检查 ffmpeg 是否可用"""
    path = find_ffmpeg()
    if not path:
        return False
    try:
        subprocess.run([path, '-version'], capture_output=True, timeout=5, check=True)
        return True
    except Exception:
        return False
