# patents-validate

校验专利 pipeline 数据库的跨表一致性。

## 命令

```bash
# 使用默认数据库和输出路径
zero run patents-validate

# 指定数据库
zero run patents-validate --db my_pipeline.sqlite --output-md _brief/my-validate.md --output-json _brief/my-validate.json
```

## 输出

- Markdown 报告：`_brief/patents-validate.md`
- JSON 结果：`_brief/patents-validate.json`

## 依赖

- Python 3.10+
- `patents/pipeline/patent_pipeline.local.sqlite`
