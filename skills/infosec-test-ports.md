# infosec-test-ports

测试深信服 SASE 平台所需端口连通性。

## 命令

```bash
zero run infosec-test-ports
```

## 测试端口

- `edrinterconnection.sangfor.com.cn:443`
- `edrinterconnection.sangfor.com.cn:8083`
- `edrinterconnection.sangfor.com.cn:54120`

## 输出

每行一个端口状态：`OK` / `TIMEOUT` / `FAILED`
