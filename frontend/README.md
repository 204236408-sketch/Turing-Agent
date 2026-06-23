# 前端

技术方案指定使用原生 HTML、CSS、JavaScript，保留 `version-b` 页面结构和视觉效果。

- `version-b.html`：系统入口
- `styles.css`：全局样式
- `app.js`：页面渲染、交互、Mock 数据与接口封装
- `assets/`：图片、图标与静态资源

前端请求统一通过 `app.js` 中的请求封装调用 `/api`，禁止在页面模块中散落后端地址。

