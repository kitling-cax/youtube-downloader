#!/usr/bin/env python3
"""YouTube Downloader CLI"""

import argparse
import sys
import os
import threading
import queue

from core.downloader import VideoDownloader
from core.video_info import fetch_video_info, format_duration, format_filesize
from utils.config import get_output_dir, set_output_dir, load_config, get_proxy


def list_formats(url: str, proxy: str = None):
    """列出所有可用格式"""
    print("\nFetching video info...")
    try:
        info = fetch_video_info(url, proxy=proxy)
        print(f"\nTitle: {info['title']}")
        print(f"Duration: {format_duration(info['duration'])}")
        print(f"Uploader: {info['uploader']}")
        print(f"\nAvailable Formats:")
        print("-" * 70)
        print(f"{'ID':<10} {'Resolution':<12} {'Ext':<6} {'Size':<12} {'Type'}")
        print("-" * 70)

        seen_resolutions = set()
        for fmt in info['formats']:
            resolution = fmt['resolution']
            if resolution in seen_resolutions:
                continue
            seen_resolutions.add(resolution)

            size = format_filesize(fmt['filesize']) if fmt['filesize'] else 'N/A'
            vcodec = fmt['vcodec']
            acodec = fmt['acodec']
            if vcodec == 'none' and acodec != 'none':
                fmt_type = 'Audio'
            elif acodec == 'none' and vcodec != 'none':
                fmt_type = 'Video'
            elif vcodec != 'none' and acodec != 'none':
                fmt_type = 'Video+Audio'
            else:
                fmt_type = 'Unknown'

            print(f"{fmt['format_id']:<10} {resolution:<12} {fmt['ext']:<6} {size:<12} {fmt_type}")

        print("-" * 70)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def download_video(url: str, format_id: str, output_dir: str = None, proxy: str = None):
    """下载视频"""
    if output_dir is None:
        output_dir = get_output_dir()

    os.makedirs(output_dir, exist_ok=True)

    print(f"\nDownloading to: {output_dir}")
    print(f"Format: {format_id}")
    if proxy:
        print(f"Proxy: {proxy}")

    downloader = VideoDownloader(output_dir, proxy=proxy)
    cancel_event = threading.Event()
    last_percent = -1

    def progress_callback(d):
        nonlocal last_percent
        if d['status'] == 'downloading':
            percent_str = d.get('_percent_str', '0%')
            try:
                percent = float(percent_str.rstrip('%'))
            except:
                percent = 0
            # 只在进度变化时打印
            if int(percent) != last_percent:
                last_percent = int(percent)
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                downloaded = d.get('_downloaded_bytes_str', '0B')
                total = d.get('_total_bytes_str', 'N/A')
                print(f"\r  {percent_str} | {speed} | ETA: {eta} | {downloaded}/{total}", end='', flush=True)

    try:
        print("\nStarting download...")
        title = downloader.download(url, format_id, progress_callback, cancel_event)
        print(f"\n\nDownload complete: {title}")
        return True
    except Exception as e:
        print(f"\n\nDownload failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='YouTube Video Downloader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --url "https://www.youtube.com/watch?v=..."
  python cli.py --url "https://www.youtube.com/watch?v=..." --format "720p"
  python cli.py --url "https://www.youtube.com/watch?v=..." --list-formats
  python cli.py --url "https://www.youtube.com/watch?v=..." --output "D:/Videos"
        """
    )

    parser.add_argument('--url', '-u', type=str,
                        help='YouTube video URL')
    parser.add_argument('--format', '-f', type=str, default='best',
                        help='Format to download (format_id or quality like "720p"). Default: best')
    parser.add_argument('--list-formats', '-l', action='store_true',
                        help='List all available formats')
    parser.add_argument('--output', '-o', type=str,
                        help='Output directory')
    parser.add_argument('--proxy', '-p', type=str,
                        help='Proxy server (e.g., http://127.0.0.1:7890)')

    args = parser.parse_args()

    if not args.url:
        parser.print_help()
        sys.exit(1)

    if args.list_formats:
        success = list_formats(args.url, proxy=args.proxy)
        sys.exit(0 if success else 1)

    if args.output:
        set_output_dir(args.output)

    proxy = args.proxy if args.proxy else get_proxy()
    success = download_video(args.url, args.format, proxy=proxy)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
