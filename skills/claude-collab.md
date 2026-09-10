# claude-collab

编排两个独立 Claude Code 实例（master/worker）通过文件总线协作。

## 命令

```bash
# 单机 demo：启动 worker 侧（无人值守）
zero run claude-collab -Role worker

# 另一个窗口启动 master 侧并下发任务
zero run claude-collab -Role master -Kickoff "实现把 bus.jsonl 转成 HTML 时间线的脚本"

# 跨机：把 -Bus 指向同步盘
zero run claude-collab -Role worker -Bus "\\NAS\claude-bus"
```

## 参数

- `-Role <master|worker>`：角色
- `-Bus <path>`：bus 目录，默认本机 `tools/claude-collab/bus`
- `-Kickoff <text>`：master 首轮任务
- `-PollSeconds <int>`：轮询间隔
- `-MaxTurns <int>`：最大轮数
- `-ClaudeTimeoutSec <int>`：单次 Claude 超时
- `-ClaudeExe <path>`：claude 可执行文件路径

## 产物

- `tools/claude-collab/bus/bus.jsonl`
- `tools/claude-collab/bus/master.session`
- `tools/claude-collab/bus/worker.session`
