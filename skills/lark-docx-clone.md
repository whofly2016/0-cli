# lark-docx-clone

把飞书/ Lark 云文档克隆到本地 Markdown 或 txt。

## 命令

```bash
# 查看帮助
zero run lark-docx-clone --help

# 按关键词搜索并克隆
zero run lark-docx-clone --search-key "VRSK" --out-dir 1_optix/lark_sync

# 按 token 克隆
zero run lark-docx-clone --token docx_xxx --out-dir 1_optix/lark_sync

# 更新已有清单
zero run lark-docx-clone --manifest 1_optix/lark_sync/manifest.json --refresh
```

## 常用参数

- `--search-key <text>`：按标题关键词搜索
- `--search-count <int>`：返回数量，默认 20
- `--token <docx_token>`：直接指定文档 token
- `--out-dir <path>`：输出目录
- `--format <txt|md>`：输出格式，默认 txt
- `--manifest <path>`：使用/生成清单文件
- `--refresh`：基于清单刷新
- `--server <server>`：lark-cli server 配置，默认 `lark-company`
- `--use-uat`：使用用户身份，默认开启

## 依赖

- `lark-cli` 已登录
- Node.js
