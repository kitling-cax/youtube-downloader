# 🤝 贡献流程（PR 流程说明）

本项目采用 **Fork + Pull Request** 工作流，欢迎任何形式的贡献（修 Bug、加功能、写文档、提 Issue）。

---

## 📌 快速流程图

```
┌─────────────────┐
│ 1. Fork 本仓库  │  ← 在 GitHub 网页右上角点 "Fork"
└────────┬────────┘
         ↓
┌─────────────────┐
│ 2. Clone 到本地 │  ← git clone <你的 fork 地址>
└────────┬────────┘
         ↓
┌─────────────────┐
│ 3. 创建特性分支 │  ← git checkout -b feature/xxx
└────────┬────────┘
         ↓
┌─────────────────┐
│ 4. 编写代码     │  ← 改完后 git add . && git commit
└────────┬────────┘
         ↓
┌─────────────────┐
│ 5. 推送到 fork  │  ← git push origin feature/xxx
└────────┬────────┘
         ↓
┌─────────────────┐
│ 6. 创建 PR      │  ← 在 GitHub 网页点 "Compare & pull request"
└────────┬────────┘
         ↓
┌─────────────────┐
│ 7. 等待 Review  │  ← 维护者审阅，可能要求修改
└────────┬────────┘
         ↓
┌─────────────────┐
│ 8. 合并到 main  │  ← 审阅通过后维护者合并
└─────────────────┘
```

---

## 🚀 详细步骤

### 1. Fork 仓库

打开 https://github.com/kitling-cax/youtube-downloader ，点右上角的 **Fork** 按钮。

这会在你的账号下创建一个副本（`https://github.com/<你的用户名>/youtube-downloader`）。

### 2. Clone 到本地

```bash
git clone https://github.com/<你的用户名>/youtube-downloader.git
cd youtube-downloader
```

### 3. 关联上游仓库（保持与原仓库同步）

```bash
git remote add upstream https://github.com/kitling-cax/youtube-downloader.git
git remote -v
# 应该看到 origin（你的 fork）和 upstream（原仓库）两个
```

### 4. 创建特性分支

**永远不要直接在 main 上改代码**，一定要新建分支：

```bash
# 先同步最新代码
git checkout main
git pull upstream main

# 创建分支（命名规范见下）
git checkout -b feature/playlist-progress-bar
# 或
git checkout -b fix/gui-crash-on-empty-url
```

#### 分支命名规范

| 类型 | 前缀 | 示例 |
|------|------|------|
| 新功能 | `feature/` | `feature/add-youtube-short` |
| Bug 修复 | `fix/` | `fix/cookie-load-error` |
| 文档 | `docs/` | `docs/update-readme` |
| 重构 | `refactor/` | `refactor/split-downloader` |
| 性能 | `perf/` | `perf/cache-thumbnail` |

### 5. 编写代码并提交

```bash
# 改完文件后
git add .
git commit -m "feat: 添加播放列表下载进度条"
```

#### Commit 信息规范（推荐遵循 Conventional Commits）

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feat:` | 新功能 | `feat: 支持 YouTube Shorts` |
| `fix:` | 修 Bug | `fix: 修复 cookie 路径找不到的崩溃` |
| `docs:` | 文档 | `docs: 补充 CLI 参数说明` |
| `style:` | 格式（不影响代码） | `style: 统一缩进` |
| `refactor:` | 重构 | `refactor: 拆分 downloader.py` |
| `perf:` | 性能优化 | `perf: 缩略图改为懒加载` |
| `test:` | 测试 | `test: 添加 video_info 单元测试` |
| `chore:` | 杂项 | `chore: 升级 yt-dlp 到 2024.5.1` |

### 6. 推送到你的 Fork

```bash
git push origin feature/playlist-progress-bar
```

### 7. 创建 Pull Request

1. 打开你 fork 的 GitHub 页面（`https://github.com/<你的用户名>/youtube-downloader`）
2. GitHub 通常会自动弹出 **"Compare & pull request"** 按钮，点它
3. **目标分支**确认是 `kitling-cax/youtube-downloader` 的 `main`
4. 填写 PR 标题和描述，参考下面的模板
5. 点 **Create pull request**

#### PR 描述模板

```markdown
## 改动类型
- [ ] 新功能
- [ ] Bug 修复
- [ ] 文档更新
- [ ] 重构

## 改动内容
<!-- 简述你做了什么 -->

## 测试方式
<!-- 怎么验证你的改动有效？ -->

## 截图 / 录屏（如果是 GUI 改动）
<!-- 粘贴图片 -->

## 关联 Issue
<!-- 如果有相关 issue，写 closes #123 -->
```

### 8. 等待审阅 + 持续同步

Reviewer 可能会要求你修改：

```bash
# 改完后
git add .
git commit -m "fix: 根据 review 修改 xxx"
git push origin feature/playlist-progress-bar
# PR 会自动更新，不用重新创建
```

如果 main 分支在你开发期间有更新，先同步再 push：

```bash
git checkout main
git pull upstream main
git checkout feature/playlist-progress-bar
git rebase main
git push origin feature/playlist-progress-bar --force-with-lease
```

### 9. 合并

审阅通过后由维护者合并到 main。**你的贡献会出现在更新日志里** 🎉

---

## ⚠️ 注意事项

### 🔒 绝对不要提交的内容

- ❌ `cookie.txt` / `cookie_a.txt` / `cookie_b.txt`（任何 cookie 文件）
- ❌ `.env`、API key、token
- ❌ 个人配置文件
- ❌ 大文件（视频、截图、构建产物）

项目根目录的 `.gitignore` 已经帮你挡了大部分，但请**主动检查**你 `git add` 的文件。

**提交前必做：**
```bash
git status
# 确认 stage 列表里没有 cookie、.env、.venv 等
```

### 🧪 代码风格

- 遵循 PEP 8
- 函数/类加 docstring
- 复杂逻辑加注释
- 避免单行超过 100 字符

### 🐛 提 Issue

发现 Bug 或想提建议？直接在 https://github.com/kitling-cax/youtube-downloader/issues 提 Issue。

Issue 模板：
- **标题**：简洁描述问题
- **复现步骤**：怎么触发这个 Bug
- **期望行为**：应该怎么表现
- **实际行为**：实际怎么表现的
- **环境**：操作系统、Python 版本、yt-dlp 版本
- **日志/截图**

---

## 💬 联系方式

有问题先提 Issue，比直接私聊更容易被其他人搜索到和帮忙解决。

