# lark-cli-work

用公司飞书 profile 执行 lark-cli 命令。

## 命令

```bash
# 搜索公司文档
zero run lark-cli-work docs search "VRSK"

# 查多维表格
zero run lark-cli-work base record-list --app-token APP_TOKEN --table-id TABLE_ID

# 发消息到公司群
zero run lark-cli-work im +messages-send --chat-id CHAT_ID --text "hello"
```

## 依赖

- `lark-cli` 已安装
- `company` profile 已登录

## 注意

- 直接映射到 `lark-cli --profile company <args>`
- 若 `company` token 过期，先 `zero run lark-cli-work auth login`
