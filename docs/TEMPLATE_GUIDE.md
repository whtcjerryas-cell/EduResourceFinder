# K12教育资源搜索系统 - 模板开发指南

## 概述

本系统使用统一的模板继承架构，所有页面都继承自 `base_new.html`，确保UI一致性和代码可维护性。

## 模板架构

### 基础模板

**文件**: `/templates/base_new.html`

**功能**:
- 统一的侧边栏导航
- Toast通知系统
- 移动端菜单支持
- 可访问性功能（ARIA标签、键盘导航）
- 响应式布局

### CSS文件结构

```
/static/css/
├── base-styles.css       # CSS变量、基础样式、重置
├── components.css        # 可复用组件（按钮、卡片、表单、表格）
└── sidebar_styles.css    # 侧边栏特定样式
```

### JavaScript文件

```
/static/js/
└── base-scripts.js       # 核心功能（Toast、侧边栏切换、移动菜单）
```

## 创建新页面

### 基本模板结构

所有页面模板都应遵循以下结构：

```html
{% extends "base_new.html" %}

{% block title %}页面标题 - K12教育资源搜索系统{% endblock %}

{% block page_css %}
<style>
    /* 页面特定的CSS样式 */
    /* 使用CSS变量确保一致性 */
    
    .my-component {
        background: var(--bg-card);
        padding: var(--spacing-lg);
        border-radius: var(--border-radius);
    }
</style>
{% endblock %}

{% block content %}
<div class="container">
    <!-- 页面内容 -->
    <div class="card">
        <h1>页面标题</h1>
        <p>页面内容</p>
    </div>
</div>
{% endblock %}

{% block page_scripts %}
<script>
    // 页面特定的JavaScript
    
    // Toast通知示例
    toast.success('成功', '操作成功完成');
    toast.error('错误', '操作失败');
</script>
{% endblock %}
```

## 可用的CSS变量

### 颜色系统

```css
--primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--primary-color: #667eea;
--success-color: #48bb78;
--warning-color: #ed8936;
--danger-color: #f56565;
--info-color: #4299e1;

/* 文本颜色 */
--text-primary: #2d3748;
--text-secondary: #718096;
--text-muted: #a0aec0;

/* 背景颜色 */
--bg-primary: #f5f7fa;
--bg-secondary: #ffffff;
--bg-card: #ffffff;
--bg-sidebar: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
```

### 间距系统

```css
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 16px;
--spacing-lg: 24px;
--spacing-xl: 32px;
```

### 字体大小

```css
--font-xs: 0.75rem;
--font-sm: 0.875rem;
--font-base: 1rem;
--font-lg: 1.125rem;
--font-xl: 1.25rem;
--font-2xl: 1.5rem;
--font-3xl: 1.875rem;
```

### 其他

```css
--border-radius: 8px;
--border-color: #e2e8f0;
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
--transition-fast: 150ms ease-in-out;
--transition-base: 200ms ease-in-out;
--sidebar-width: 180px;
```

## 可复用组件类

### 卡片

```html
<div class="card">
    <h1>卡片标题</h1>
    <p>卡片内容</p>
</div>
```

### 按钮

```html
<button class="btn btn-primary">主要按钮</button>
<button class="btn btn-secondary">次要按钮</button>
<button class="btn btn-success">成功按钮</button>
<button class="btn btn-danger">危险按钮</button>
```

### 表单

```html
<form>
    <div class="form-group">
        <label for="input">标签</label>
        <input type="text" id="input" class="form-control" placeholder="请输入...">
    </div>
    <button type="submit" class="btn btn-primary">提交</button>
</form>
```

### 表格

```html
<table class="table">
    <thead>
        <tr>
            <th>列1</th>
            <th>列2</th>
            <th>列3</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>数据1</td>
            <td>数据2</td>
            <td>数据3</td>
        </tr>
    </tbody>
</table>
```

### 徽章

```html
<span class="badge badge-primary">主要</span>
<span class="badge badge-success">成功</span>
<span class="badge badge-warning">警告</span>
<span class="badge badge-danger">危险</span>
```

## JavaScript功能

### Toast通知

```javascript
// 成功通知
toast.success('成功', '操作成功完成');

// 错误通知
toast.error('错误', '操作失败');

// 警告通知
toast.warning('警告', '请注意');

// 信息通知
toast.info('信息', '这是提示信息');
```

### 侧边栏

侧边栏切换自动处理，无需手动编写代码。

### 移动菜单

移动菜单在屏幕宽度 < 768px 时自动显示汉堡菜单按钮。

## 响应式设计

### 断点

- 移动端: < 768px
- 平板: 768px - 1024px
- 桌面: > 1024px

### 移动端适配

所有组件都是响应式的，但建议在移动设备上测试。

```css
@media (max-width: 768px) {
    /* 移动端特定样式 */
    .my-component {
        padding: var(--spacing-sm);
    }
}
```

## 可访问性

### ARIA标签

系统自动添加基本的ARIA标签，但对于自定义组件，建议添加：

```html
<button aria-label="关闭对话框">×</button>
<div role="status" aria-live="polite">状态信息</div>
```

### 键盘导航

所有交互元素都支持键盘导航：
- Tab: 焦点移动
- Enter/Space: 激活按钮和链接
- Esc: 关闭模态框和菜单

## 最佳实践

### 1. 使用CSS变量

始终使用CSS变量而不是硬编码值：

```css
/* ✅ 好的做法 */
padding: var(--spacing-lg);
background: var(--bg-card);

/* ❌ 避免这样做 */
padding: 24px;
background: #ffffff;
```

### 2. 保持内容结构清晰

```html
<div class="container">
    <div class="card">
        <h1>标题</h1>
        <div class="content">
            <!-- 内容 -->
        </div>
    </div>
</div>
```

### 3. 使用Toast而不是alert

```javascript
// ✅ 好的做法
toast.success('成功', '操作完成');

// ❌ 避免这样做
alert('操作完成');
```

### 4. 始终测试移动端

在开发过程中，定期在移动设备或浏览器开发者工具中测试响应式布局。

### 5. 保持JavaScript模块化

将复杂功能分解为函数：

```javascript
function loadData() {
    // 加载数据逻辑
}

function displayData(data) {
    // 显示数据逻辑
}

function handleError(error) {
    // 错误处理逻辑
    toast.error('错误', error.message);
}

// 主要逻辑
async function init() {
    try {
        const data = await loadData();
        displayData(data);
    } catch (error) {
        handleError(error);
    }
}

init();
```

## 迁移现有页面

如果需要迁移旧页面到新架构：

1. 删除 `<html>`, `<head>`, `<body>` 标签
2. 添加 `{% extends "base_new.html" %}`
3. 提取页面特定样式到 `{% block page_css %}`
4. 提取页面内容到 `{% block content %}`
5. 提取页面脚本到 `{% block page_scripts %}`
6. 删除重复的侧边栏和Toast代码
7. 将硬编码的CSS替换为CSS变量
8. 测试所有功能

## 故障排除

### 样式不生效

1. 检查是否正确引用了CSS变量
2. 清除浏览器缓存
3. 检查CSS选择器优先级

### JavaScript错误

1. 检查浏览器控制台
2. 确保在页面脚本之前加载了base-scripts.js
3. 检查变量名拼写

### 响应式布局问题

1. 检查是否使用了固定宽度
2. 确保使用flexbox或CSS Grid
3. 测试不同屏幕尺寸

## 示例页面

查看以下文件了解实际应用：

- `/templates/evaluation_reports.html` - 简单列表页面
- `/templates/knowledge_points.html` - Chart.js图表页面
- `/templates/global_map.html` - Leaflet地图页面
- `/templates/compare.html` - 复杂交互页面

## 支持

如有问题，请参考：
- `/docs/CSS_GUIDE.md` - CSS设计系统文档
- `/templates/base_new.html` - 基础模板源码
- `/static/css/base-styles.css` - CSS变量定义

最后更新: 2026-01-07
