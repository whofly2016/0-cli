# tools/0-cli — 本地 CLI-Anything Hub

为 `0_docs` 工作区提供统一的本地 CLI 发现、调用和 AI 可读说明书入口。

目标：让 AI 通过聊天即可发现并调用这台电脑上的工具。

## 安装

```bash
pip install -e tools/0-cli
```

## 用法

```bash
zero list                   # 列出本地已注册 CLI
zero list --json            # 以 JSON 输出注册表
zero list --category productivity
zero list --status wrapper --json
zero info work-manager      # 查看工具详情
zero info work-manager --json
zero skill work-manager     # 查看 skill 文档
zero run work-manager query --tasks --status overdue --json
zero run work-manager --version --dry-run

# 如果要把以 -- 开头的参数传给工具本身（而非 zero run），使用 -- 分隔
zero run lark-docx-clone -- --help
zero search dashboard       # 按关键词搜索
zero search dashboard --skill   # 同时搜索 SKILL.md 内容
zero search ai --category productivity --json
zero install work-manager   # 运行 install_cmd
zero doctor                 # 校验 registry 与本地文件一致性
zero doctor --json          # JSON 输出校验结果
zero scan                   # 扫描 workspace 中的 cli-anything-registry.json
zero scan --json            # JSON 输出扫描结果
zero brief                  # 生成人生简报（等价于 zero run life-brief）
zero brief --offline --days 7 --out _brief/life-week.md
```

## 注册新工具

1. 在 `local_registry.json` 的 `entries` 里新增条目
2. 在 `skills/<name>.md` 或原工具目录 `skills/SKILL.md` 写入 AI 说明书
3. 运行 `zero doctor` 校验

### Entry 字段

- `name`: 工具唯一标识
- `display_name`, `version`, `description`, `category`
- `status`: `ready` / `wrapper` / `documented`（`documented` 仅作为文档，不可 `zero run`）
- `skill_md`: AI 说明书路径
- `install_cmd`: 安装命令（可选）
- `invoke_template`: 调用模板，`{args}` 会被替换为传入参数；`documented` 状态可省略

## 设计原则

- **先发现、再调用**：每个工具必须有 `SKILL.md` 和 `invoke_template`
- **不重写，先包装**：已有 PowerShell / Python / Node 脚本优先做 wrapper
- **JSON 优先**：逐步给常用命令加上 `--json`，方便 AI 解析
