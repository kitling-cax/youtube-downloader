# 📊 项目状态记录

> 本文档记录项目在 GitHub 上的发布状态、本地状态以及关键里程碑。
> 最后更新：2026-06-07

---

## 🌐 GitHub 仓库

| 项目 | 值 |
|------|-----|
| 仓库地址 | https://github.com/kitling-cax/youtube-downloader |
| 仓库所有者 | kitling-cax |
| 远程地址 | https://github.com/kitling-cax/youtube-downloader.git |
| 默认分支 | `main` |
| 可见性 | Public |

---

## 🏷️ Release 状态

| 项目 | 值 |
|------|-----|
| **最新 Release** | v1.1.0 |
| Release 标题 | v1.0.0 - 首次发布 |
| 发布时间 | 2026-06-07 06:09:29 UTC |
| Release URL | https://github.com/kitling-cax/youtube-downloader/releases/tag/v1.0.0 |
| 状态 | ✅ 已发布（非草稿、非预发布） |
| 最新 commit | `39a2f93` |

---

## 📦 提交历史（GitHub 远端）

| Commit | Tag | 说明 |
|--------|-----|------|
| `39a2f93` | — | fix: fetch_video_info 也跳过无效视频 + 清理 ANSI 颜色码 |
| `e60355e` | — | fix: 下载时也跳过无效视频 |
| `b5fe575` | — | refactor: 视频列表改为独立弹窗 |
| `91de981` | — | fix: 播放列表获取跳过无效视频 |
| `570d28e` | — | docs: 添加 STATUS.md |
| `d16cdd7` | — | docs: 添加 CONTRIBUTING.md |
| `4aff71d` | **v1.0.0** | docs: 更新 README - cookie 路径迁移 |
| `43cd347` | — | Initial commit: YouTube Downloader |

---

## ✨ 功能特性

### 核心功能
- 🎬 多平台支持：YouTube、Bilibili 单视频 / 播放列表 / 系列
- 📋 播放列表批量下载 + 勾选选择
- 🎚️ 多分辨率：360p / 480p / 720p / 1080p
- 🔀 音视频自动合并（内置 ffmpeg）
- 🍪 Cookie 认证（用户目录）
- 🌐 HTTP/SOCKS 代理
- 🪟 玻璃拟态无边框 GUI
- ⌨️ CLI 模式（适合脚本批处理）

### 容错能力
- ✅ 播放列表获取跳过无效视频（已删除/地区限制/无权限）
- ✅ 单个视频下载失败不中断整个列表
- ✅ fetch_video_info 在列表中第一个视频失效时仍能继续
- ✅ GUI 弹窗显示 "成功 N 个, 跳过 M 个" 统计

### 隐私安全
- ✅ Cookie 存放在用户目录 `~/.youtube_downloader/cookie.txt`
- ✅ 仓库不含任何敏感信息、API key
- ✅ 完整的 `.gitignore` 防护
- ✅ `cookie.example.txt` 文档模板

---

## 🛡️ 防护措施

### 1. 代码层面（治本）
- `utils/config.py` → `get_default_cookie_file()` 指向用户目录
- `core/downloader.py` → `self.ydl_opts` 含 `ignoreerrors=True`
- `core/video_info.py` → `fetch_video_info` 和 `fetch_playlist_info` 都启用 `ignoreerrors`
- `ui/gui.py` → `_on_fetch_err` 清理 ANSI 颜色码

### 2. `.gitignore`（治标）
9 大类规则：敏感文件、Python 环境、打包产物、IDE 配置、调试文件、备份目录、媒体文件、Claude 本地配置、图片素材。

### 3. `cookie.example.txt`（文档）
仓库内唯一与 cookie 相关的文件，仅作模板说明。

---

## 📁 仓库内文件清单

```
.gitignore                  # Git 忽略规则
README.md                   # 项目说明
CONTRIBUTING.md             # 贡献/PR 流程
STATUS.md                   # 本文件：项目状态记录
YouTubeDownloader.spec      # PyInstaller 配置
YouTubeDownloader_GUI.spec
YouTube下载器.spec
cli.py                      # CLI 入口
cookie.example.txt          # Cookie 模板
main.py                     # GUI 入口
requirements.txt            # 依赖清单
core/
  ├── __init__.py
  ├── downloader.py         # yt-dlp 封装 + ignoreerrors
  └── video_info.py         # 视频信息获取 + ignoreerrors
ui/
  ├── __init__.py
  ├── gui.py                # PySide6 GUI + PlaylistDialog
  └── (PlaylistDialog 独立弹窗类)
utils/
  ├── __init__.py           # ffmpeg 探测等
  └── config.py             # 配置 + 用户目录路径
```

---

## 📊 仓库统计

| 项目 | 数值 |
|------|------|
| 文件总数（仓库内）| 14 |
| 代码行数（含文档）| ~2500 |
| 主要语言 | Python |
| UI 框架 | PySide6 |
| 下载引擎 | yt-dlp |

---

## 🔨 构建状态

| 项目 | 值 |
|------|-----|
| 可执行文件 | `dist/YouTube下载器/YouTube下载器.exe` |
| exe 大小 | 8.6 MB |
| 目录总大小 | 332.5 MB（含 ffmpeg）|
| 构建工具 | PyInstaller 6.20.0 |
| 打包耗时 | ~80 秒 |
| Spec 文件 | YouTube下载器.spec |
| 启动测试 | ✅ 正常 |

---

## ✅ 关键里程碑

- [x] 2026-04-28：项目初版
- [x] 2026-05-20：单文件 GUI 版本
- [x] 2026-05-26：spec 升级为打包 ffmpeg 的目录模式
- [x] 2026-06-05：修复 GUI 播放列表列表不可见 Bug
- [x] 2026-06-05：新增播放列表加载错误弹窗
- [x] **2026-06-07：首次发布到 GitHub（v1.0.0）**
- [x] **2026-06-07：cookie 路径迁移到用户目录（隐私安全升级）**
- [x] **2026-06-07：添加 .gitignore、CONTRIBUTING.md、STATUS.md**
- [x] **2026-06-07：视频列表改为独立弹窗（解决溢出问题）**
- [x] **2026-06-07：修复播放列表/下载容错（跳过无效视频）**
- [x] **2026-06-07：修复 fetch_video_info + 清理 ANSI 颜色码**

---

## 🐛 已修复 Bug 汇总

| Bug | 根因 | 修复 | Commit |
|-----|------|------|--------|
| GUI 视频列表与原界面重叠 | 60 视频溢出 600x450 固定窗口 | 改为独立 QDialog 弹窗 | `b5fe575` |
| 78 视频列表获取失败 | yt-dlp 遇到 1 个失效视频就中断 | 添加 `ignoreerrors=True` | `91de981` |
| 下载时遇到 1 个失效视频中断整个列表 | 下载逻辑未启用 ignoreerrors | 下载器 ydl_opts 添加 `ignoreerrors` | `e60355e` |
| GUI 仍然报"获取失败" | fetch_video_info 没改 | 给 fetch_video_info 也添加 ignoreerrors | `39a2f93` |
| 错误信息带 ANSI 颜色码 `[0;31m` | yt-dlp 终端彩色输出 | 禁用颜色 + UI 层正则清理 | `39a2f93` |

---

## 🔄 后续维护建议

- [ ] 添加单元测试（`tests/` 目录）
- [ ] 添加 GitHub Actions CI
- [ ] 添加 LICENSE 文件
- [ ] 添加 Issue 模板（`.github/ISSUE_TEMPLATE/`）
- [ ] 把打包好的 exe 上传到 GitHub Release
- [ ] 监控 yt-dlp 版本兼容性
- [ ] v1.0.1：打新包并更新 Release（包含最新弹窗 + 容错修复）

---

## 🔧 本地维护命令速查

```bash
# 拉取最新代码
git pull origin main

# 提交修改
git add .
git commit -m "类型: 描述"
git push origin main

# 查看状态
git status
git log --oneline --decorate --all

# 重新打包
.venv/Scripts/python.exe -m PyInstaller "YouTube下载器.spec" --clean --noconfirm

# 创建新版本
git tag -a v1.1.0 -m "v1.1.0 描述"
git push origin v1.1.0
# 然后去 GitHub 网页创建对应 Release

# 删除 tag（万一打错）
git tag -d v1.0.0
git push origin --delete v1.0.0
```

---

**📌 文档生成日期：** 2026-06-07
