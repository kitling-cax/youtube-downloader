# 🐱 YouTube & B站 下载器

一个基于 `yt-dlp` + `PySide6` 的视频下载工具，支持 YouTube、Bilibili 单视频和合集下载，提供玻璃拟态 GUI 和命令行两种使用方式。

## ✨ 功能特性

- 🎬 **多平台支持**：YouTube、Bilibili（单视频 / 合集 / 系列）
- 📋 **播放列表批量下载**：自动识别合集，可视化勾选要下载的视频
- 🎚️ **多分辨率选择**：360p / 480p / 720p / 1080p（需大会员 cookie）
- 🔀 **音视频自动合并**：内置 ffmpeg，无需手动处理
- 🍪 **Cookie 认证**：支持自定义 cookie 文件，登录后可下大会员画质
- 🌐 **代理支持**：HTTP/SOCKS 代理可配置
- 🪟 **无边框玻璃拟态 GUI**：自定义拖拽、圆角、动画
- ⌨️ **CLI 模式**：适合脚本批处理

## 📁 项目结构

```
youtube_download/
├── main.py                  # GUI 入口
├── cli.py                   # 命令行入口
├── requirements.txt         # 依赖
├── cookie.example.txt       # Cookie 模板（真实 cookie 不入库）
├── bin/ffmpeg.exe           # 内置 ffmpeg（音视频合并）
├── core/
│   ├── downloader.py        # yt-dlp 封装，支持单视频/播放列表
│   └── video_info.py        # 视频信息获取 + 格式化工具
├── ui/gui.py                # PySide6 无边框玻璃拟态窗口
├── utils/
│   ├── config.py            # 配置 + 用户目录路径解析
│   └── __init__.py          # ffmpeg 探测、Referer 提取
├── dist/YouTube下载器/      # 打包产物
├── YouTube下载器.spec       # PyInstaller 打包配置（主用）
├── YouTubeDownloader_GUI.spec
└── YouTubeDownloader.spec
```

## 🚀 快速开始

### GUI 模式

```bash
python main.py
```

操作流程：
1. 粘贴视频/合集链接
2. 点击「🔍 获取」
3. 等待解析完成（合集需几秒到几十秒）
4. 单视频：选分辨率 → 下载
5. 合集：在 60 个视频列表里勾选要下的 → 选分辨率 → 下载

### CLI 模式

```bash
# 单视频
python cli.py -u "https://www.bilibili.com/video/BV17HmqBDEwg" -f 1080p

# 合集（season 类型）
python cli.py -u "https://space.bilibili.com/3546377359461153/lists/7049090?type=season" -f 1080p

# 列出所有可用格式
python cli.py -u "..." --list-formats

# 指定输出目录
python cli.py -u "..." -o "D:\Videos"

# 使用代理
python cli.py -u "..." -p "http://127.0.0.1:7890"
```

## 🔧 关键技术点

| 模块 | 说明 |
|------|------|
| `VideoDownloader.download` | 单视频下载，支持 best / 分辨率 / format_id |
| `VideoDownloader.download_playlist` | 播放列表下载，支持 `playlist_items` 选中索引 |
| `_build_format_opts` | 根据有无 ffmpeg 智能选 mp4 + m4a 合并 / 单文件 |
| `fetch_video_info` | 自动识别 playlist/multi_video 类型，取首个视频做主信息 |
| `fetch_playlist_info` | 列出合集所有视频的标题/URL/时长 |
| `find_ffmpeg` | 优先 PATH → PyInstaller `_MEIPASS/bin` → 项目 `bin/` |
| `check_ffmpeg_available` | 用 `ffmpeg -version` 验证可用性 |
| 配置持久化 | `~/.youtube_downloader_config.json` 保存 output_dir 和 proxy |

## 🍪 Cookie 配置

**B 站**：需要登录态才能下载高清视频。从浏览器导出 Netscape 格式 cookie：

1. 浏览器装「Get cookies.txt LOCALLY」或「Cookie-Editor」扩展
2. 登录 bilibili.com 后导出
3. **必须是纯 Netscape 格式**（不能混 JSON）
4. 把导出的文件保存到 **`~/.youtube_downloader/cookie.txt`**（即 `C:\Users\<你>\.youtube_downloader\cookie.txt`）
5. GUI 启动会自动读取这个路径

**YouTube**：大多视频免登录即可，部分需要登录验证。

> ⚠️ **不要把 cookie 文件提交到 Git**。本项目把 cookie 放在用户主目录的隐藏文件夹里，从源头避免泄露。`cookie.example.txt` 仅为文档模板。

## ⚠️ Cookie 格式注意事项

yt-dlp 只接受 **Netscape 格式**的 cookie 文件。Cookie-Editor 导出的文件常常混入了 JSON 数组，会导致：

```
http.cookiejar.LoadError: invalid length
CookieLoadError: failed to load cookies
```

**清洗方法**（保留 Netscape 行，删掉 JSON 部分）：

```python
# 删除 JSON 数组部分（从 '[\n    {' 开始到文件末尾）
```

或者用 yt-dlp 推荐方式：浏览器装扩展「Get cookies.txt LOCALLY」直接导出纯 Netscape 格式。

## 🛠️ 已修复的 Bug

| Bug | 原因 | 修复 |
|-----|------|------|
| GUI 加载播放列表失败被静默吞掉 | `_on_playlist_load_err` 只写一行日志 | 改为弹 `QMessageBox` 提示 |
| `_on_playlist_loaded` 处理 60 个视频时列表被挤 | 用 `QComboBox` 下拉，60 项不可见 | 改为 `QListWidget` 复选框列表 |
| 单 BV 链接误判为合集 | `_type` 是 `None` 而非 `playlist` | 现在通过 `is_playlist` 字段判断 |
| Cookie 双重格式导致 yt-dlp 拒载 | Netscape + JSON 混合 | 清洗为纯 Netscape 格式 |

## 📦 打包

```bash
python -m PyInstaller "YouTube下载器.spec" --clean --noconfirm
```

输出：`dist/YouTube下载器/YouTube下载器.exe`（主程序 9 MB，含 ffmpeg 总 334 MB）

分发时**整个文件夹**一起打包（PyInstaller 目录模式非单文件）。

## 📝 依赖

```
yt-dlp>=2024.0.0
PySide6>=6.5.0
Pillow>=10.0.0
```

打包还需要：PyInstaller>=6.0

## 🐾 调试技巧

**验证 cookie 是否有效**（命令空间一行出结果）：

```python
python -X utf8 -c "
from core.video_info import fetch_video_info
info = fetch_video_info('BV_URL', cookie_file='cookie.txt')
print('is_playlist =', info.get('is_playlist'))
print('playlist_count =', info.get('playlist_count'))
for f in info.get('formats', []):
    if f['vcodec'] != 'none' or f['acodec'] != 'none':
        print(f'  {f[\"resolution\"]} {f[\"format_id\"]} {f[\"filesize\"]/1024/1024:.1f}MB')
"
```

**GUI 日志探针**：UI 内置 `[DBG] is_playlist=...` / `[DBG] _on_playlist_loaded 收到 N 个` 日志，问题卡哪步一目了然。

## 📜 版本历史

- **v1.0.0** (2026-06-07)：首次发布到 GitHub
  - 修复 GUI 播放列表不可见问题，改为 QListWidget
  - 新增播放列表加载错误弹窗
  - **重要：cookie 路径从项目内 `cookie.txt` 迁移到用户目录 `~/.youtube_downloader/cookie.txt`**，从源头避免泄露
  - 添加 `.gitignore`、PR 流程文档
- 2026-05-26：spec 升级为打包 ffmpeg 的目录模式
- 2026-05-20：单文件 GUI 版本
- 2026-04-28：初版
