# feishu-helper

飞书 Chrome 扩展，用于弥补飞书 Open API 不支持的浏览器端操作。

## 用途

- 文件夹权限批量设置
- 文档批量操作
- 其他只能由浏览器端完成的飞书 Web 界面自动化

## 使用方式

1. 打开 Chrome 扩展管理页面：`chrome://extensions`
2. 开启开发者模式
3. 加载已解压的扩展：`tools/feishu-helper`
4. 在飞书 Web 页面上使用扩展功能

## 注意

- 不是 CLI 工具，无法通过 `zero run` 调用
- 修改后需点击扩展页面「重新加载」
