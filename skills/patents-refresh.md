# patents-refresh

刷新专利机会的评分、评审包、报告和站点数据。

## 命令

```bash
# 刷新 P0/P1 机会
zero run patents-refresh --run-dir runs/zero-2026-09-10

# 刷新所有机会
zero run patents-refresh --all --run-dir runs/zero-2026-09-10

# 指定机会
zero run patents-refresh --opportunity-id opp_xxx --run-dir runs/zero-2026-09-10
```

## 常用参数

- `--db <path>`：数据库路径
- `--run-dir <path>`：输出目录，**必填**
- `--opportunity-id <id>`：指定机会（可多次）
- `--all`：所有机会
- `--priority <P0|P1|...>`：优先级带，默认 P0/P1
- `--site-out <path>`：生成 site/data.js 的路径

## 产物

- `runs/<run-dir>/score-report-<id>.md`
- `runs/<run-dir>/review-package-<id>.md`
- `runs/<run-dir>/opportunity-structure-draft.*`
- `patents/pipeline/site/data.js`
