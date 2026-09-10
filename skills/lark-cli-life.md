# lark-cli-life

用个人飞书（life）profile 执行 lark-cli 命令，管理工作/生活/人生相关事务。

## 首次配置

1. 在个人飞书租户创建/获取自建应用，得到 `App ID` 和 `App Secret`。
2. 添加 profile：

   ```powershell
   $secret = '你的 App Secret'
   $secret | lark-cli profile add --name life --app-id cli_你的_Personal_AppID --brand feishu --app-secret-stdin --use
   ```

3. 登录：

   ```bash
   lark-cli auth login --profile life --domain all
   ```

## 命令

```bash
# 搜索个人文档
zero run lark-cli-life docs search "2026 旅行"

# 查个人多维表格
zero run lark-cli-life base record-list --app-token APP_TOKEN --table-id TABLE_ID

# 发消息到个人群
zero run lark-cli-life im +messages-send --chat-id CHAT_ID --text "hello"
```

## 依赖

- `lark-cli` 已安装
- `life` profile 已添加并登录

## 注意

- 直接映射到 `lark-cli --profile life <args>`
- 工作/生活边界靠 profile 隔离，避免把个人数据写进公司飞书，或反之
