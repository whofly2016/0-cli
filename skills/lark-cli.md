# lark-cli

官方 Lark/Feishu CLI，已支持多 profile，适合公司/个人双账号切换。

## 当前 profile

```bash
lark-cli profile list
```

现有 profile：

- `company`：Optix 公司飞书，当前 active，token valid
- `feishu-mcp`：MCP 用 app，未登录

## 添加个人飞书 profile

1. 在飞书开放平台（国内：https://open.feishu.cn/app；国际：https://open.larksuite.com/app）
   创建/获取一个自建应用，得到 `App ID` 和 `App Secret`。

2. 添加 profile：

   ```bash
   # 把 SECRET 替换成真实值
   $secret = '你的 App Secret'
   $secret | lark-cli profile add --name personal --app-id cli_xxxxxxxxxxxxxxxx --brand feishu --app-secret-stdin --use
   ```

   如果是国际版 Lark，把 `--brand` 改成 `lark`。

3. 登录：

   ```bash
   lark-cli auth login --profile personal --domain all
   ```

   这会弹出一个 device flow 授权链接，用个人飞书账号扫码/确认。

## 切换 profile

```bash
# 切换到公司
lark-cli profile use company

# 切换到个人
lark-cli profile use personal

# 快速切回上一个（上班/下班 toggle）
lark-cli profile use -
```

## 临时指定 profile 执行命令

```bash
lark-cli --profile personal docs search "关键词"
lark-cli --profile company base record-list --app-token XXX --table-id YYY
```

## 通过 zero 调用

```bash
zero run lark-cli -- profile list
zero run lark-cli -- --profile company docs search "VRSK"
```

> 注意：因为 `zero run` 本身也解析 `--`，所以传 `--profile` 这类参数时用 `--` 分隔。

## 重要提示

- 不要通过语音/聊天泄露 `App Secret`；命令输入时用安全方式粘贴。
- token 存在系统 keychain/credential store；`lark-cli auth logout` 会清除对应 profile 的 token。
