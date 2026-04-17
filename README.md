# 考研剧本杀 · 联合归档处

四本桌面知识推理剧本杀（**101 政治 / 201 英语 / 301 数学 / 408 计算机**），合计 **24 展区 · 202 房间 · 202 枚知识徽章 · 4 位馆长**。纯前端 · PWA · 离线可玩 · 可加手机主屏。

## 在线试玩

> 🔗 部署后填入 GitHub Pages 地址：`https://<user>.github.io/考研剧本杀/考研剧本杀合集/`

**手机添加到主屏**：
- iOS Safari：分享按钮 → **添加到主屏幕**
- Android Chrome：三点菜单 → **添加到主屏幕** / **安装应用**
- 添加后即离线可用，各科独立存档。

## 本地运行

```bat
双击 C:\mq\启动手机服务.bat
```

`.bat` 会调用 `启动手机服务.py`，自动：
- 过滤虚拟网卡 IP
- 终端打印扫码二维码（指向局域网 IP）
- 自动打开默认浏览器
- 启动 `python -m http.server 8080`

手机与电脑同 Wi-Fi 时扫码即可访问。

## 项目结构

```
/
├── 考研剧本杀合集/          # 启动器（四学科卡片 · 各科进度条）
├── 101剧本杀/              # 政治 · 红宝书 · 5 展区 × 44 房间 · 馆长 沈藏心
├── 201剧本杀/              # 英语 · 千卷之书 · 6 展区 × 45 房间 · 馆长 石漪兰
├── 301剧本杀/              # 数学 · 微言玄卷 · 9 展区 × 65 房间 · 馆长 陈若虚
├── 408剧本杀/              # 计算机 · 墨语之卷 · 4 展区 × 48 房间 · 馆长 林溯涟
│
├── shared/                 # 共享层（真相源，脚本分发到各科 data/）
│   ├── boot.js             #   错误边界 + 键盘无障碍 + SW 注册
│   ├── engine.js           #   Web Audio 音效 + 多轨 BGM + 通用工具
│   └── game.js             #   存档 (localStorage v2) + Sidebar 增量渲染
│
├── 启动手机服务.py / .bat   # 本地 HTTP 服务 + 二维码 + 浏览器自动打开
└── _*.py                   # 构建脚本（见下）
```

每科目录内：

```
<subject>/
├── XXX剧本杀.html          # HTML：BGM_TRACKS + state + FOLLOWUPS + PROLOGUE + DEDUCTION_QS + render 函数
├── manifest.json           # PWA manifest（scope='../' 打通跨科跳转）
├── sw.js                   # Service Worker（cache-first 离线策略）
├── icon.svg / icon-192.png / icon-512.png
└── data/
    ├── boot.js             # shared/boot.js 副本
    ├── engine.js           # shared/engine.js 副本
    ├── game.js             # shared/game.js 副本
    └── rooms.js            # ZONES + ROOMS（题库）
```

## 开发：修改代码的工作流

| 想改什么 | 改哪里 | 然后跑 |
|---|---|---|
| 共用的音效/BGM/工具 | `shared/engine.js` | `python _sync_engine.py` |
| 共用的存档/侧边栏 | `shared/game.js` | `python _sync_game.py` |
| 共用的引导/SW 注册 | `shared/boot.js` | `python _sync_boot.py` |
| 某科的题目/房间数据 | `<subject>/data/rooms.js` | 无需同步，刷新即可 |
| 某科的叙事/推理/render | `<subject>/<subject>剧本杀.html` | 无需同步，刷新即可 |
| 图标 | `_gen_icons.py` 参数 | `python _gen_icons.py` |

所有 `_*.py` 脚本**幂等**，重复执行安全：每次会 bump 对应 SW 版本号强制客户端更新缓存。

## 技术细节

- **纯前端**：无后端依赖，不需 npm / Node（开发时可选用 `node --check` 验证 JS）
- **PWA**：5 个 manifest 共享根 scope（`../`），跨科跳转不脱离独立窗口
- **离线**：每科 Service Worker 预缓存 HTML + 4 个 data/ + 3 个图标
- **存档**：localStorage v2，键名 `exam_<subject>_progress`，自动从旧键 `101_rpg_save` 迁移
- **无障碍**：`[data-kbd]` 键盘委托、`aria-label`、`:focus-visible` 金色焦点框、aria-live stage
- **BGM**：纯 Web Audio 合成，不占流量

## 历次优化（7 轮）

1. 新增 5 个 Service Worker + 离线缓存
2. SVG → PNG 图标 + manifest 规范化（iOS 主屏图标）
3. localStorage 版本化 + 命名空间 + 修复跨科共用键导致的存档相互覆盖 bug
4. 启动脚本 Python 重写（IP 过滤 + 二维码 + 浏览器自动打开）
5. 启动器各科进度卡片显示
6. 全局错误边界（防白屏）
7. PWA scope 提升（`./` → `../`）+ id 字段显式化
8. Sidebar 增量渲染（DOM 缓存 + diff 更新）
9. 键盘无障碍 + ARIA + focus ring
10. 题库抽到 `data/rooms.js`（改题无需编辑 230KB HTML）
11. 共享层抽取 Phase 1-3：`boot.js` / `engine.js` / `game.js`

每科 HTML 从 **230KB 降到 103-141KB**（政治 101 较大因叙事最长）。

## 许可

本项目仅为学习/记忆辅助用途。
