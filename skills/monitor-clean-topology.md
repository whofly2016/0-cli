# monitor-clean-topology

清除 Windows 显示拓扑缓存。

## 命令

```bash
zero run monitor-clean-topology
```

## 行为

删除注册表项：

- `HKLM\...\GraphicsDrivers\Configuration`
- `HKLM\...\GraphicsDrivers\Connectivity`
- `HKLM\...\GraphicsDrivers\ScaleFactors`

## 注意

- **必须以管理员身份运行**
- 运行后**必须重启电脑**
