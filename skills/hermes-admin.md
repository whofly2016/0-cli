# hermes-admin

通过 WinRM/WSL 带外管理 254（`WIN-2P75GKG124R`）上 WSL 里运行的 **hermes** 飞书 MCP 群管理机器人。

## 命令

```bash
zero run hermes-admin status         # 体检：WinRM + 身份 + WSL + hermes 进程/端口
zero run hermes-admin exec 'whoami'  # 在 254 Windows 上执行 PowerShell
zero run hermes-admin wsl 'uname -a' # 在 254 的 WSL 里执行 bash
zero run hermes-admin logs           # tail hermes 日志
zero run hermes-admin restart        # 重启 hermes 服务
zero run hermes-admin rdp            # 打开 RDP 远程到 254
zero run hermes-admin save-cred      # 重新保存 WinRM 凭证
```

## 依赖

- PowerShell 7（`pwsh`）
- WinRM 端口 5985 到 192.168.9.254 可达
- 凭证已用 DPAPI 加密保存到 `tools/hermes-admin/.secrets/server.cred`

## 注意

- 业务数据不走本通道，本通道只用于运维 254 上的 hermes 宿主
- 中文/引号命令已通过 base64 双向封装，任意字符都能传透到远端
- ICMP ping 被防火墙拦截不能作为离线判断依据
