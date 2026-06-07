import os
import yt_dlp

from utils import get_referer
from utils.config import get_default_cookie_file


def fetch_video_info(url: str, proxy: str = None, cookie_file: str = None) -> dict:
    """获取视频信息，返回包含标题、时长、格式等信息的字典"""
    if cookie_file is None:
        cookie_file = get_default_cookie_file()
    opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': get_referer(url),
        },
    }
    if os.path.exists(cookie_file):
        opts['cookiefile'] = cookie_file
    if proxy:
        opts['proxy'] = proxy

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

        # 如果是播放列表类型，取第一个视频的信息
        if info.get('_type') in ('playlist', 'multi_video'):
            entries = info.get('entries', [])
            if entries and len(entries) > 0:
                first_video = entries[0]
                if first_video:
                    info = first_video
                    info['is_playlist'] = True
                    info['playlist_count'] = len(entries)
                else:
                    info['is_playlist'] = False
                    info['playlist_count'] = 0
            else:
                info['is_playlist'] = False
                info['playlist_count'] = 0
        else:
            info['is_playlist'] = False
            info['playlist_count'] = 0

        formats = []
        for fmt in info.get('formats', []):
            format_info = {
                'format_id': fmt.get('format_id', ''),
                'ext': fmt.get('ext', ''),
                'resolution': 'N/A',
                'filesize': fmt.get('filesize') or fmt.get('filesize_approx') or 0,
                'tbr': fmt.get('tbr', 0),
                'vcodec': fmt.get('vcodec', 'none'),
                'acodec': fmt.get('acodec', 'none'),
            }
            if fmt.get('height'):
                format_info['resolution'] = f"{fmt['height']}p"
            elif fmt.get('resolution'):
                format_info['resolution'] = fmt['resolution']
            formats.append(format_info)

        return {
            'title': info.get('title', 'Unknown'),
            'duration': info.get('duration', 0) or 0,
            'thumbnail': info.get('thumbnail', ''),
            'description': info.get('description', ''),
            'uploader': info.get('uploader', ''),
            'view_count': info.get('view_count', 0),
            'upload_date': info.get('upload_date', ''),
            'formats': formats,
            'is_playlist': info.get('is_playlist', False),
            'playlist_count': info.get('playlist_count', 0),
        }


def fetch_playlist_info(url: str, proxy: str = None, cookie_file: str = None) -> list:
    """获取播放列表中所有视频的信息"""
    if cookie_file is None:
        cookie_file = get_default_cookie_file()
    opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': False,
        'ignoreerrors': True,  # 关键：跳过列表中无效/被删除/地区限制的视频，而不是让整个列表获取失败
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': get_referer(url),
        },
    }
    if os.path.exists(cookie_file):
        opts['cookiefile'] = cookie_file
    if proxy:
        opts['proxy'] = proxy

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info is None:
            # 整个列表获取都失败（极端情况，比如 cookie 失效）
            return []
        entries = info.get('entries', [])
        videos = []
        skipped = 0
        for i, entry in enumerate(entries):
            if not entry:
                # entry 为 None 通常是视频被删除/地区限制/无访问权限
                skipped += 1
                continue
            videos.append({
                'index': len(videos) + 1,  # 用实际数量作为新索引，跳过无效项
                'title': entry.get('title', 'Unknown'),
                'url': entry.get('url') or entry.get('webpage_url', ''),
                'duration': entry.get('duration', 0),
                'id': entry.get('id', ''),
            })
        if skipped:
            print(f"[playlist] 跳过 {skipped} 个无效视频（已删除/地区限制/无权限）")
        return videos


def format_duration(seconds: int) -> str:
    """将秒数转换为 HH:MM:SS 格式"""
    if not seconds:
        return "00:00:00"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_filesize(bytes_size: int) -> str:
    """将字节数转换为人类可读格式"""
    if not bytes_size:
        return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"
