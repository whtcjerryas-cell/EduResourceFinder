# 搜索和Excel导出功能解耦

## 问题描述

用户报告：搜索2个及以上年级/学科时会出现内存不足导致崩溃。用户希望将搜索和Excel导出功能解耦，方便排查问题。

## 解决方案

### 功能解耦

**之前**：
- 批量搜索完成后自动导出Excel
- 搜索和导出耦合在一起，难以排查问题

**现在**：
- 搜索按钮：只负责搜索（单个或批量）
- Excel导出按钮：独立按钮，手动触发导出
- 搜索和导出完全解耦

### 修改内容

#### 1. 移除批量搜索的自动导出

**文件**: `templates/index.html`

**修改前**:
```javascript
// 批量搜索完成后自动导出Excel
await exportBatchResultsToExcel(allResults);
```

**修改后**:
```javascript
// 🔥 不再自动导出Excel，改为手动导出（解耦搜索和导出功能）
console.log('批量搜索完成，共 ' + allResults.length + ' 个结果，等待用户手动导出Excel');
```

#### 2. 更新批量搜索确认对话框

**修改前**:
```javascript
if (!confirm('...所有结果将自动导出到Excel文件。\n\n是否继续？')) {
```

**修改后**:
```javascript
if (!confirm('...搜索完成后，请点击右上角"📊 Excel"按钮手动导出结果。\n\n是否继续？')) {
```

#### 3. 统一Excel导出函数

**文件**: `templates/index.html`

**修改后**:
```javascript
// 导出Excel（统一入口，自动判断是单个搜索还是批量搜索）
async function exportResultsToExcel() {
    if (!currentResults || currentResults.length === 0) {
        toast.warning('导出失败', '没有可导出的结果');
        return;
    }

    // 🔥 判断是否是批量搜索结果
    var isBatchResult = currentResults.length > 0 && (
        currentResults[0].hasOwnProperty('country') || 
        currentResults[0].hasOwnProperty('grade') || 
        currentResults[0].hasOwnProperty('subject')
    );
    
    // 如果结果数量较多（>50），或者明确是批量搜索结果，使用批量导出API
    if (isBatchResult || currentResults.length > 50) {
        await exportBatchResultsToExcel(currentResults);
    } else {
        // 单个搜索结果，使用简单的CSV导出
        var content = convertToCSV(currentResults);
        // ... CSV导出逻辑
    }
}
```

#### 4. 更新提示信息

**修改前**:
```javascript
toast.info('批量搜索完成', '...正在导出Excel...');
noticeDiv.innerHTML = '...完整结果已导出到Excel';
```

**修改后**:
```javascript
toast.success('批量搜索完成', '...点击"📊 Excel"按钮导出');
noticeDiv.innerHTML = '...点击右上角"📊 Excel"按钮导出完整结果';
```

## 使用流程

### 单个搜索
1. 选择1个年级 + 1个学科
2. 点击"🚀 开始搜索"
3. 搜索完成后，点击"📊 Excel"按钮导出（使用简单CSV导出）

### 批量搜索
1. 选择多个年级或学科
2. 点击"🚀 开始搜索"
3. 搜索完成后，点击"📊 Excel"按钮导出（使用批量Excel导出API）

## 优势

1. **问题隔离**
   - 搜索和导出完全分离
   - 可以单独测试搜索功能
   - 可以单独测试导出功能

2. **内存管理**
   - 搜索完成后不立即导出，减少内存压力
   - 用户可以选择是否导出
   - 导出失败不影响搜索结果

3. **用户体验**
   - 用户可以查看搜索结果后再决定是否导出
   - 可以多次导出（如果第一次失败）
   - 导出过程更可控

## 排查问题

### 如果搜索2个及以上年级/学科时崩溃

**排查步骤**：
1. 执行批量搜索（不点击导出按钮）
2. 观察是否崩溃
   - 如果崩溃 → 问题在搜索功能
   - 如果不崩溃 → 问题在导出功能

3. 如果搜索正常，点击导出按钮
4. 观察是否崩溃
   - 如果崩溃 → 问题在Excel导出功能
   - 如果不崩溃 → 问题已解决

### 日志检查

**搜索日志**：
```bash
tail -f search_system.log | grep -E "搜索|search"
```

**导出日志**：
```bash
tail -f search_system.log | grep -E "导出|export|Excel"
```

## 相关文件

- `templates/index.html` - 前端搜索和导出逻辑

## 修复日期

2026-01-08

