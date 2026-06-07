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
| **最新 Release** | v1.0.0 |
| Release 标题 | v1.0.0 - 首次发布 |
| 发布时间 | 2026-06-07 06:09:29 UTC |
| Release URL | https://github.com/kitling-cax/youtube-downloader/releases/tag/v1.0.0 |
| 状态 | ✅ 已发布（非草稿、非预发布） |

---

## 📦 提交历史（GitHub 远端）

| Commit | Tag | 说明 |
|--------|-----|------|
| `d16cdd7` | — | docs: 添加 CONTRIBUTING.md 贡献流程说明 |
| `4aff71d` | **v1.0.0** | docs: 更新 README - cookie 路径迁移到用户目录 |
| `43cd347` | — | Initial commit: YouTube Downloader |

---

## 🔐 隐私/安全状态

| 检查项 | 状态 |
|--------|------|
| 仓库内 cookie.txt | ✅ 不存在 |
| 仓库内 cookie_a.txt | ✅ 不存在 |
| 仓库内 cookie_b.txt | ✅ 不存在 |
| 仓库内 .env / API key | ✅ 不存在（已扫描） |
| 仓库内 .claude/ 本地配置 | ✅ 不存在（已忽略） |
| 仓库内 .venv/ 虚拟环境 | ✅ 不存在（已忽略） |
| 仓库内 build/ dist/ 产物 | ✅ 不存在（已忽略） |
| 仓库内 backup_*/ 旧备份 | ✅ 不存在（已忽略） |
| 仓库内大文件（视频/截图）| ✅ 不存在（已忽略） |

**Cookie 存放位置：** `C:\Users\kitling\.youtube_downloader\cookie.txt`（用户目录，不在项目内）

---

## 🛡️ 已实施的防护措施

### 1. 代码层面（治本）
- `utils/config.py` → `get_default_cookie_file()` 指向用户目录
- `core/downloader.py` → 默认从 `get_default_cookie_file()` 读取
- `core/video_info.py` → 默认从 `get_default_cookie_file()` 读取
- `ui/gui.py` → GUI 启动自动定位用户目录 cookie

### 2. `.gitignore`（治标）
包含 9 大类规则：敏感文件、Python 环境、打包产物、IDE 配置、调试文件、备份目录、媒体文件、Claude 本地配置、图片素材。

### 3. `cookie.example.txt`（文档）
仓库内唯一与 cookie 相关的文件，仅作模板说明，**不包含任何真实凭据**。

---

## 📁 项目结构（仓库内）

```
youtube_download/
├── .gitignore                  # Git 忽略规则
├── README.md                   # 项目说明
├── CONTRIBUTING.md             # 贡献/PR 流程
├── STATUS.md                   # 本文件：项目状态记录
├── YouTubeDownloader.spec      # PyInstaller 配置
├── YouTubeDownloader_GUI.spec
├── YouTube下载器.spec
├── cli.py                      # CLI 入口
├── cookie.example.txt          # Cookie 模板（文档）
├── main.py                     # GUI 入口
├── requirements.txt            # 依赖清单
├── core/
│   ├── __init__.py
│   ├── downloader.py           # yt-dlp 封装
│   └── video_info.py           # 视频信息获取
├── ui/
│   ├── __init__.py
│   └── gui.py                  # PySide6 GUI
└── utils/
    ├── __init__.py             # ffmpeg 探测等
    └── config.py               # 配置 + 用户目录路径
```

---

## 📊 仓库统计

| 项目 | 数值 |
|------|------|
| 文件总数 | 16 |
| 代码行数 | ~1921（不含文档）|
| 主要语言 | Python |
| UI 框架 | PySide6 |
| 下载引擎 | yt-dlp |
| License | （未指定） |

---

## ✅ 已完成的关键里程碑

- [x] 2026-04-28：项目初版
- [x] 2026-05-20：单文件 GUI 版本
- [x] 2026-05-26：spec 升级为打包 ffmpeg 的目录模式
- [x] 2026-06-05：修复 GUI 播放列表列表不可见 Bug
- [x] 2026-06-05：新增播放列表加载错误弹窗
- [x] **2026-06-07：首次发布到 GitHub（v1.0.0）**
- [x] **2026-06-07：cookie 路径迁移到用户目录（隐私安全升级）**
- [x] **2026-06-07：添加 .gitignore、CONTRIBUTING.md、STATUS.md**

---

## 🔄 后续维护建议

- [ ] 添加单元测试（`tests/` 目录）
- [ ] 添加 GitHub Actions CI
- [ ] 添加 LICENSE 文件
- [ ] 添加 Issue 模板（`.github/ISSUE_TEMPLATE/`）
- [ ] 考虑发版时附带打包好的 exe（PyInstaller）
- [ ] 监控 yt-dlp 版本兼容性

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
