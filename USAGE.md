# Profile README Kit

一套可跑的个人主页模板，思路来自 [MeChen618](https://github.com/MeChen618) 的 profile 仓库：
**用 SMIL 动画 SVG 撑起页面，用每天一次的 Actions 刷新数据**，全程零依赖、零 JS。

这个目录是独立的，不参与 `hk4e_go` 的 Go 构建，可以整体拖到别处用。

## 文件结构

```
profile.json                     # 唯一数据源：文案、配色、终端台词、仓库
README.md                        # 由 profile.json 生成（不要手改）
scripts/build.py                 # 入口：生成全部资源
scripts/svg_kit.py               # 共享的 SVG 小组件（窗口边框 / 打字机 / 缓动条）
scripts/gen_card.py              # 角色卡 820x300
scripts/gen_terminal.py          # 打字机终端
scripts/gen_console.py           # 实时数据面板（GitHub API）
scripts/gen_readme.py            # 从 config 渲染 README.md
scripts/snapshot.py              # 把动画冻结成静态终态帧
scripts/check.py                 # 布局冒烟测试（栅格化 + 像素统计）
.github/workflows/profile.yml    # 每天构建并发布到 output 分支
```

## 三步上手

1. 建一个和用户名同名的仓库 `<user>/<user>`，把本目录内容拷进去。
2. 改 `profile.json`：`user.name` / `user.handle` / `tracked_repo` / 终端台词 / 技能条。
3. 本地生成并提交：

```bash
python3 scripts/build.py          # 需要联网抓 tracked_repo 的实时数据
python3 scripts/check.py          # 可选：布局校验（需 rsvg-convert + Pillow）
git add -A && git commit -m "profile: init" && git push
```

推上去之后 Actions 会自动跑一次，把 `dist/` 发到 `output` 分支，README 里的图就活了。
**注意**：`gen_readme.py` 假设仓库名等于用户名（profile 仓库的约定）；仓库名不同时改 `gen_readme.py` 里的 `raw` 拼接。

## 本地预览

```bash
python3 scripts/build.py --offline     # 不联网，用样例数字
open dist/snapshot/character-card.svg  # 定格帧，静态查看器里也能看
open dist/terminal.svg                 # 浏览器打开才有动画
```

想要一个带开关的预览页：

```bash
python3 -m http.server 8765 --bind 127.0.0.1   # 在 kit 目录下执行
# 打开 http://127.0.0.1:8765/preview/
```

[preview/index.html](preview/index.html) 是一个零依赖的查看器：动画/定格切换、深浅背景切换、
宽度滑杆（对应 README 里的 `width="100%"`）、重播按钮，还有一块按 GitHub 排版渲染 `README.md`
的区域（会把 output 分支的 raw 链接自动换成本地 `dist/` 产物）。

`dist/*.svg` 是带 SMIL 动画的正式产物；`dist/snapshot/*.svg` 是把动画"烘焙"成终态的静态版
（删掉动画元素、把终值回填到属性上），给不支持 SMIL 的查看器、og:image、截图用。

## 配置字段

| 字段 | 说明 |
|---|---|
| `user.name` / `user.handle` | 名字、GitHub 用户名 |
| `user.initial` | 徽记中间那个字母，留空则取名字首字母 |
| `user.tagline` / `tagline_cn` | 角色卡副标题（中英各行一个） |
| `user.star_rating` | 名字右侧星星数量 |
| `user.badges[]` | shields.io 徽章：`label` `value` `color` `logo` `href` |
| `user.stack` | skillicons 图标列表 `["python","go",...]` |
| `tracked_repo` | 数据面板追踪的仓库，格式 `owner/repo` |
| `theme` | 主色、卡片三段渐变、文字色 |
| `card.stats[]` | 属性条：`label` `value`(0-100) `color`，可选 `shown` 覆盖显示值；**条数可变，卡片高度自适应** |
| `terminal.script[]` | 逐行 `["cmd"\|"out"\|"err", 文本]` |
| `console.log[]` | 控制台日志 `["INFO"\|"WARN"\|"ERR", 文本]` |
| `emit_readme` | 是否让 build 顺带生成 `README.md` |

## 和原版相比的几处改动

- **共享模块**：窗口边框、打字机、缓动条抽到 `svg_kit.py`，原版在三个脚本里各写了一遍圆点和标题栏。
- **单一数据源**：`profile.json` 同时驱动三张图和 README，不会出现"README 改了、卡片没改"。
- **不造假数据**：原版第四张卡是写死的 `TPS 20.0` 加一条 `sin/cos` 折线；这里换成真实的 `LAST PUSH` 相对时间。
- **失败降级**：API 挂了或限流时数字显示 `—` 并打印 warning，**不让 CI 变红**（原版这一步一挂，当天整张图就停更）。
- **定格快照**：动画元素的初值是 `opacity="0"`，任何静态渲染出来都是空白——快照解决了预览和截图问题。
- **布局自检**：`check.py` 栅格化后按区域统计"有字的像素比例"，能抓到元素飞出画布、行重叠这类 XML 校验抓不到的错。

## 几个坑

- **只能用 SMIL**：GitHub 会剥掉 README 图片里的 `<script>`，`<style>` 里的 CSS 动画也不保证生效，所以动效必须写在 SVG 元素上（`<animate>` / `<animateTransform>` / `<set>`）。
- **raw 有缓存**：`raw.githubusercontent.com` 走 CDN，更新后通常要等几分钟才刷新，别以为没生效。
- **定时任务会延迟**：`schedule` 在高峰期可能晚几十分钟到几小时，动作频繁的仓库别指望准点。
- **等宽字体是估算值**：`gen_terminal.py` 里 `CHAR_W = 8.6` 是按 JetBrains Mono 14px 量的，换字体要重标，否则打字机边缘会错位。
- **中文靠系统字体**：卡片里的中文走 `PingFang SC / Microsoft YaHei / Noto Sans CJK`，Linux 上如果缺 CJK 字体会掉成方块。
- **`search/issues` 限流**：认证后 30 次/分钟，一天一次完全够用；本地反复跑注意别刷爆。
- **文字会丢连续空格**：SVG 里多个空格会被合并，需要保留用 `xml:space="preserve"`（终端用的是 `❯ ` 提示符 + 文本，不受影响）。
