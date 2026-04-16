# 长期记忆

## 葡萄酒简报项目

### 基本信息
- 项目目录：`/Users/scottwang/WorkBuddy/Claw/`
- HTML 简报文件：`wine-briefing.html`
- 飞书推送脚本：`wine_briefing_push.py`
- 自动化任务：`.codebuddy/automations/wine-daily-briefing/`

### GitHub Pages 配置（2026-03-25 完成）
- GitHub 用户名：andiloswang
- 仓库地址：https://github.com/andiloswang/wine-briefing
- **公网访问地址：https://andiloswang.github.io/wine-briefing/**
- SSH Key：`~/.ssh/id_ed25519`（ed25519，绑定 andilos@163.com）
- 本地 git remote：`git@github.com:andiloswang/wine-briefing.git`
- 飞书卡片"查看完整简报"按钮已指向上述 GitHub Pages 地址

### 推送脚本逻辑
每次运行 `wine_briefing_push.py`：
1. 自动将 `wine-briefing.html` 复制为 `index.html`
2. git commit + push 到 GitHub main 分支（无变更时跳过）
3. 推送飞书卡片消息

### 简报内容规范
- 三个模块：核心App更新 / 学习教育工具 / 行业重要新闻
- 新闻时效：优先72小时内
- 期数：每期+1，当前为第七期（2026-04-07）
- 酒红色 HTML 设计风格
