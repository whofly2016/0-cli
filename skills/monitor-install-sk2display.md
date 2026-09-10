# monitor-install-sk2display

安装 SK2Display 8K DSC 显示器 INF 驱动。

## 命令

```bash
zero run monitor-install-sk2display
```

## 注意

- **必须以管理员身份运行**
- 脚本会调用 `pnputil /add-driver /install`
- 安装后建议到设备管理器卸载原监视器设备再重新插拔或重启
- 依赖 `tools/monitor/scripts/driver/gpt/8k/SK2Display_8K_DSC.inf`
