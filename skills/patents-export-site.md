# patents-export-site

生成专利 pipeline 网站数据。

## 命令

```bash
zero run patents-export-site
```

## 行为

从 `patents/pipeline/patent_pipeline.local.sqlite` 读取数据，生成 `patents/pipeline/site/data.js`。

## 依赖

- Python 3.10+
- `patents/pipeline/patent_pipeline.local.sqlite`

## 产物

- `patents/pipeline/site/data.js`
- 可用浏览器打开 `patents/pipeline/site/index.html`
