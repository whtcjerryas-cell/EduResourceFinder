# K12教育资源搜索系统 - CSS设计系统文档

## 概述

本系统使用基于CSS变量的模块化设计系统，确保所有页面UI一致、易维护且响应式。

## CSS文件结构

```
/static/css/
├── base-styles.css       # 核心CSS变量、基础样式、重置
├── components.css        # 可复用组件（按钮、卡片、表单、表格）
└── sidebar_styles.css    # 侧边栏特定样式
```

## 颜色系统

### 主色调

```css
--primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--primary-color: #667eea;        /* 主色 */
--primary-light: #7f9ef5;        /* 浅主色 */
--primary-dark: #5a67d8;         /* 深主色 */
```

### 语义颜色

```css
--success-color: #48bb78;        /* 成功 - 绿色 */
--warning-color: #ed8936;        /* 警告 - 橙色 */
--danger-color: #f56565;         /* 危险 - 红色 */
--info-color: #4299e1;           /* 信息 - 蓝色 */
```

### 文本颜色

```css
--text-primary: #2d3748;         /* 主要文本 */
--text-secondary: #718096;       /* 次要文本 */
--text-muted: #a0aec0;           /* 弱化文本 */
--text-inverse: #ffffff;         /* 反色文本 */
```

### 背景颜色

```css
--bg-primary: #f5f7fa;           /* 主背景 */
--bg-secondary: #ffffff;         /* 次要背景 */
--bg-card: #ffffff;              /* 卡片背景 */
--bg-sidebar: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
--bg-overlay: rgba(0, 0, 0, 0.5); /* 遮罩层 */
```

### 边框和阴影

```css
--border-color: #e2e8f0;
--border-radius: 8px;
--border-radius-sm: 4px;
--border-radius-lg: 12px;
--border-radius-full: 9999px;

--shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15);
```

## 间距系统

### Scale

```css
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 16px;
--spacing-lg: 24px;
--spacing-xl: 32px;
--spacing-2xl: 48px;
--spacing-3xl: 64px;
```

### 使用示例

```css
/* 内边距 */
padding: var(--spacing-md);
padding: var(--spacing-lg) var(--spacing-xl);

/* 外边距 */
margin: var(--spacing-sm);
margin-bottom: var(--spacing-lg);

/* 间隙 */
gap: var(--spacing-md);
```

## 字体系统

### 字体大小

```css
--font-xs: 0.75rem;      /* 12px */
--font-sm: 0.875rem;     /* 14px */
--font-base: 1rem;       /* 16px */
--font-lg: 1.125rem;     /* 18px */
--font-xl: 1.25rem;      /* 20px */
--font-2xl: 1.5rem;      /* 24px */
--font-3xl: 1.875rem;    /* 30px */
--font-4xl: 2.25rem;     /* 36px */
```

### 字重

```css
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
--font-extrabold: 800;
```

### 字体家族

```css
--font-family-base: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
--font-family-mono: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Mono', 'Droid Sans Mono',
    'Source Code Pro', monospace;
```

## 布局系统

### 容器

```css
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: var(--spacing-xl) 20px;
}
```

### Flexbox工具类

```css
.d-flex { display: flex; }
.flex-row { flex-direction: row; }
.flex-column { flex-direction: column; }
.justify-content-start { justify-content: flex-start; }
.justify-content-center { justify-content: center; }
.justify-content-end { justify-content: flex-end; }
.justify-content-between { justify-content: space-between; }
.align-items-start { align-items: flex-start; }
.align-items-center { align-items: center; }
.align-items-end { align-items: flex-end; }
.flex-wrap { flex-wrap: wrap; }
```

### Grid工具类

```css
.d-grid { display: grid; }
.grid-template-columns-1 { grid-template-columns: repeat(1, 1fr); }
.grid-template-columns-2 { grid-template-columns: repeat(2, 1fr); }
.grid-template-columns-3 { grid-template-columns: repeat(3, 1fr); }
.grid-template-columns-auto { 
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
}
```

## 组件样式

### 按钮

#### 基础样式

```css
.btn {
    display: inline-block;
    padding: 12px 24px;
    font-size: var(--font-base);
    font-weight: 600;
    text-align: center;
    border: none;
    border-radius: var(--border-radius);
    cursor: pointer;
    transition: all var(--transition-base);
}
```

#### 变体

```css
.btn-primary {
    background: var(--primary-gradient);
    color: white;
}

.btn-secondary {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 2px solid var(--border-color);
}

.btn-success {
    background: var(--success-color);
    color: white;
}

.btn-danger {
    background: var(--danger-color);
    color: white;
}
```

#### 状态

```css
.btn:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

.btn:active {
    transform: translateY(0);
}

.btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}
```

### 卡片

```css
.card {
    background: var(--bg-card);
    padding: var(--spacing-lg);
    border-radius: var(--border-radius);
    box-shadow: var(--shadow-md);
    transition: all var(--transition-base);
}

.card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-2px);
}
```

### 表单

```css
.form-group {
    margin-bottom: var(--spacing-md);
}

.form-group label {
    display: block;
    margin-bottom: var(--spacing-sm);
    font-weight: 600;
    color: var(--text-primary);
}

.form-control {
    width: 100%;
    padding: 12px;
    border: 2px solid var(--border-color);
    border-radius: var(--border-radius);
    font-size: var(--font-base);
    transition: all var(--transition-fast);
}

.form-control:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}
```

### 表格

```css
.table {
    width: 100%;
    border-collapse: collapse;
}

.table thead {
    background: var(--bg-primary);
}

.table th {
    padding: var(--spacing-md);
    text-align: left;
    font-weight: 600;
    color: var(--text-primary);
    border-bottom: 2px solid var(--border-color);
}

.table td {
    padding: var(--spacing-md);
    border-bottom: 1px solid var(--border-color);
}

.table tbody tr:hover {
    background: var(--bg-primary);
}
```

### 徽章

```css
.badge {
    display: inline-block;
    padding: 4px 12px;
    font-size: var(--font-xs);
    font-weight: 600;
    border-radius: var(--border-radius-full);
    color: white;
}

.badge-primary { background: var(--primary-color); }
.badge-success { background: var(--success-color); }
.badge-warning { background: var(--warning-color); }
.badge-danger { background: var(--danger-color); }
.badge-secondary { background: var(--text-secondary); }
```

## 动画和过渡

### 过渡时长

```css
--transition-fast: 150ms ease-in-out;
--transition-base: 200ms ease-in-out;
--transition-slow: 300ms ease-in-out;
```

### 常用动画

```css
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

## 响应式设计

### 断点

```css
--breakpoint-sm: 640px;
--breakpoint-md: 768px;
--breakpoint-lg: 1024px;
--breakpoint-xl: 1280px;
```

### 媒体查询

```css
/* 移动端优先 */
@media (min-width: 768px) {
    /* 平板及更大 */
}

@media (min-width: 1024px) {
    /* 桌面及更大 */
}

/* 桌面优先 */
@media (max-width: 767px) {
    /* 移动端 */
}

@media (max-width: 1023px) {
    /* 平板及更小 */
}
```

## 可访问性

### 焦点样式

```css
*:focus {
    outline: 2px solid var(--primary-color);
    outline-offset: 2px;
}

button:focus {
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3);
}
```

### 跳转链接

```css
.skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    background: var(--primary-color);
    color: white;
    padding: 8px;
    z-index: 100;
}

.skip-link:focus {
    top: 0;
}
```

## 最佳实践

### 1. 始终使用CSS变量

```css
/* ✅ 好的做法 */
padding: var(--spacing-lg);
background: var(--bg-card);
color: var(--text-primary);

/* ❌ 避免这样做 */
padding: 24px;
background: #ffffff;
color: #2d3748;
```

### 2. 使用相对单位

```css
/* ✅ 好的做法 */
font-size: var(--font-base);
padding: var(--spacing-md);

/* ❌ 避免这样做 */
font-size: 16px;
padding: 16px;
```

### 3. 移动端优先

```css
/* ✅ 好的做法 - 从移动端开始，逐步增强 */
.component {
    padding: var(--spacing-md);
}

@media (min-width: 768px) {
    .component {
        padding: var(--spacing-lg);
    }
}

/* ❌ 避免这样做 - 从桌面开始，逐步降级 */
.component {
    padding: var(--spacing-lg);
}

@media (max-width: 767px) {
    .component {
        padding: var(--spacing-md);
    }
}
```

### 4. 使用语义化类名

```css
/* ✅ 好的做法 */
.search-button {}
.result-item {}
.stat-card {}

/* ❌ 避免这样做 */
.blue-button {}
.box1 {}
.big-text {}
```

### 5. 避免深层嵌套

```css
/* ✅ 好的做法 */
.result-item {
    padding: var(--spacing-md);
}

.result-title {
    font-size: var(--font-lg);
    font-weight: 600;
}

/* ❌ 避免这样做 */
.result-item .result-header .result-content .result-title {
    font-size: var(--font-lg);
    font-weight: 600;
}
```

## 自定义主题

### 创建新主题

如果要创建新的配色方案，只需在 `:root` 中修改变量：

```css
:root {
    /* 深色主题示例 */
    --bg-primary: #1a202c;
    --bg-secondary: #2d3748;
    --bg-card: #2d3748;
    --text-primary: #f7fafc;
    --text-secondary: #e2e8f0;
}
```

### 组件级覆盖

```css
.special-component {
    --primary-color: #38b2ac;
    --success-color: #48bb78;
}
```

## 工具类

### 文本

```css
.text-left { text-align: left; }
.text-center { text-align: center; }
.text-right { text-align: right; }
.text-primary { color: var(--text-primary); }
.text-secondary { color: var(--text-secondary); }
.text-muted { color: var(--text-muted); }
```

### 显示

```css
.d-none { display: none; }
.d-block { display: block; }
.d-inline-block { display: inline-block; }
.d-flex { display: flex; }
```

### 间距

```css
.m-0 { margin: 0; }
.mt-1 { margin-top: var(--spacing-xs); }
.mb-2 { margin-bottom: var(--spacing-sm); }
.p-3 { padding: var(--spacing-md); }
```

## 性能优化

### CSS优化技巧

1. **避免通配符选择器**
   ```css
   /* ❌ 避免 */
   * { margin: 0; padding: 0; }
   
   /* ✅ 使用重置CSS */
   html { box-sizing: border-box; }
   *, *::before, *::after { box-sizing: inherit; }
   ```

2. **避免过于具体的选择器**
   ```css
   /* ❌ 避免 */
   div.container div.card div.content h1.title {}
   
   /* ✅ 使用类名 */
   .title {}
   ```

3. **使用will-change优化动画**
   ```css
   .animated-element {
       will-change: transform, opacity;
   }
   ```

## 浏览器兼容性

### 支持的浏览器

- Chrome/Edge: 最新2个版本
- Firefox: 最新2个版本
- Safari: 最新2个版本
- 移动浏览器: iOS Safari 12+, Chrome Android

### CSS特性

- CSS Variables: ✅ 支持
- Flexbox: ✅ 支持
- CSS Grid: ✅ 支持
- Custom Properties: ✅ 支持

## 调试技巧

### 检查CSS变量

```javascript
// 在浏览器控制台中
getComputedStyle(document.documentElement)
    .getPropertyValue('--primary-color');
```

### 查找样式来源

1. 在浏览器开发者工具中右键点击元素
2. 选择"检查元素"
3. 查看"Styles"面板，找到CSS规则的来源

### 测试响应式

1. 打开浏览器开发者工具
2. 点击设备工具栏图标（或按F12）
3. 选择不同设备或自定义屏幕尺寸

## 故障排除

### 样式不生效

1. 检查CSS变量是否正确拼写
2. 检查浏览器缓存（Ctrl/Cmd + Shift + R）
3. 检查CSS文件加载顺序
4. 检查选择器优先级

### 响应式问题

1. 检查视口meta标签是否存在
2. 检查媒体查询语法
3. 在不同设备上测试

### 性能问题

1. 减少不必要的动画
2. 使用transform代替top/left
3. 优化图片和图标
4. 减少CSS文件大小

## 资源

- [CSS Variables MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [Flexbox Guide](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)
- [Grid Guide](https://css-tricks.com/snippets/css/complete-guide-grid/)
- [Responsive Design](https://web.dev/responsive-web-design-basics/)

最后更新: 2026-01-07
