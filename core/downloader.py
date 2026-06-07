import os
import re
import yt_dlp
from yt_dlp.utils import DownloadCancelled

from utils import get_referer, find_ffmpeg, check_ffmpeg_available
from utils.config import get_default_cookie_file


class VideoDownloader:
    def __init__(self, output_dir: str = None, proxy: str = None, cookie_file: str = None):
        if output_dir is None:
            output_dir = os.path.join(os.path.expanduser("~"), "Downloads", "YouTube")
        self.output_dir = output_dir
        self.proxy = proxy
        self.has_ffmpeg = check_ffmpeg_available()
        os.makedirs(self.output_dir, exist_ok=True)
        if cookie_file is None:
            cookie_file = get_default_cookie_file()
        self.ydl_opts = {
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            # 关键：跳过列表中无效/被删除/地区限制的视频，避免一个失败中断整个下载
            'ignoreerrors': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            },
        }
        if os.path.exists(cookie_file):
            self.ydl_opts['cookiefile'] = cookie_file
        if proxy:
            self.ydl_opts['proxy'] = proxy
        ffmpeg_path = find_ffmpeg()
        if ffmpeg_path:
            self.ydl_opts['ffmpeg_location'] = os.path.dirname(ffmpeg_path)

    def _build_format_opts(self, url: str, format_id: str, opts: dict):
        """根据 URL 和 format_id 构建格式选择参数"""
        has_ffmpeg = self.has_ffmpeg

        if format_id == 'best':
            if has_ffmpeg:
                opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
            else:
                opts['format'] = 'bestvideo[ext=mp4]/best'
            return

        if format_id.endswith('p') and format_id[:-1].isdigit():
            height = format_id[:-1]
            if has_ffmpeg:
                opts['format'] = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio/bestvideo[ext=mp4]/best'
            else:
                opts['format'] = f'bestvideo[height<={height}][ext=mp4]/bestvideo[ext=mp4]/best'
        else:
            opts['format'] = f'{format_id}[ext=mp4]/{format_id}'

    def _make_progress_hook(self, progress_callback, cancel_event):
        def progress_hook(d):
            if cancel_event and cancel_event.is_set():
                raise DownloadCancelled()
            if progress_callback:
                info_data = dict(d)
                info_data['info'] = ''
                pct = 0
                percent_str = d.get('_percent_str', '')
                if percent_str:
                    match = re.search(r'(\d+\.?\d*)%', percent_str)
                    if match:
                        pct = float(match.group(1))
                elif d.get('percent'):
                    pct = float(d.get('percent')) * 100
                info_data['pct'] = pct
                if d.get('filename'):
                    info_data['info'] = os.path.basename(d.get('filename'))
                progress_callback(info_data)
        return progress_hook

    def get_video_info(self, url: str) -> dict:
        """获取视频信息"""
        opts = self.ydl_opts.copy()
        opts['quiet'] = False
        opts['no_warnings'] = False
        opts['skip_download'] = True
        opts['http_headers'] = {**opts.get('http_headers', {}), 'Referer': get_referer(url)}

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return self._parse_video_info(info)

    def get_available_formats(self, url: str) -> list:
        """获取可用格式列表"""
        info = self.get_video_info(url)
        return info.get('formats', [])

    def download(self, url: str, format_id: str = 'best',
                 progress_callback=None, cancel_event=None,
                 force_single=True) -> str:
        """下载单个视频，返回视频标题（失败返回 None）"""
        try:
            opts = self.ydl_opts.copy()
            opts['quiet'] = False
            opts['no_warnings'] = True
            opts['http_headers'] = {**opts.get('http_headers', {}), 'Referer': get_referer(url)}

            if force_single:
                opts['noplaylist'] = True

            self._build_format_opts(url, format_id, opts)
            opts['progress_hooks'] = [self._make_progress_hook(progress_callback, cancel_event)]

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # ignoreerrors=True 时 info 可能为 None（视频失效/被删除/地区限制）
                if info is None:
                    return None
                return info.get('title', 'Unknown')

        except DownloadCancelled:
            raise Exception('cancelled')

    def download_playlist(self, url: str, format_id: str = 'best',
                         progress_callback=None, cancel_event=None,
                         playlist_items=None) -> dict:
        """下载播放列表，返回 {'titles': 成功列表, 'skipped': 失败数量}
        playlist_items: 要下载的视频索引列表 (从1开始)，None表示全部

        注意：设置了 ignoreerrors=True（继承自 ydl_opts），所以列表中
        失效/被删除/地区限制的视频会自动跳过，不会中断整个下载。
        """
        try:
            opts = self.ydl_opts.copy()
            opts['quiet'] = False
            opts['no_warnings'] = True
            opts['outtmpl'] = os.path.join(self.output_dir, '%(playlist_index)s - %(title)s.%(ext)s')
            opts['http_headers'] = {**opts.get('http_headers', {}), 'Referer': get_referer(url)}

            self._build_format_opts(url, format_id, opts)

            if playlist_items:
                opts['playlist_items'] = ','.join(map(str, playlist_items))

            titles = []
            skipped = []

            def _collect_title(d):
                status = d.get('status')
                info = d.get('info_dict') or {}
                if status == 'finished':
                    title = info.get('title', '')
                    if title:
                        titles.append(title)
                elif status == 'error':
                    # 视频失败（被删除/地区限制/无权限等）
                    title = info.get('title') or 'Unknown'
                    skipped.append(title)
                    # 通过 progress_callback 通知 UI
                    if progress_callback:
                        progress_callback({
                            'pct': 0,
                            'info': f'⏭ 跳过失败: {title}',
                        })

            opts['progress_hooks'] = [
                self._make_progress_hook(progress_callback, cancel_event),
                _collect_title,
            ]

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            return {'titles': titles, 'skipped': skipped}

        except DownloadCancelled:
            raise Exception('cancelled')

    def _parse_video_info(self, info: dict) -> dict:
        """解析视频信息"""
        formats = []
        for fmt in info.get('formats', []):
            format_info = {
                'format_id': fmt.get('format_id', ''),
                'ext': fmt.get('ext', ''),
                'resolution': fmt.get('resolution', 'N/A'),
                'filesize': fmt.get('filesize') or fmt.get('filesize_approx') or 0,
                'tbr': fmt.get('tbr', 0),
                'vcodec': fmt.get('vcodec', 'none'),
                'acodec': fmt.get('acodec', 'none'),
            }
            if fmt.get('height'):
                format_info['resolution'] = f"{fmt['height']}p"
            formats.append(format_info)

        return {
            'title': info.get('title', 'Unknown'),
            'duration': info.get('duration', 0),
            'thumbnail': info.get('thumbnail', ''),
            'description': info.get('description', ''),
            'formats': formats,
        }
