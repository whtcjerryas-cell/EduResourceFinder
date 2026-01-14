# 小批量验证测试说明

## 快速开始

### 方法 1: 使用示例数据查看 HTML 效果

已经生成了示例 HTML 文件，可以直接查看：

```bash
# 在浏览器中打开
open test_playlists.html

# 或手动打开文件
file:///Users/shmiwanghao8/Desktop/education/Indonesia/test_playlists.html
```

### 方法 2: 运行完整测试（需要 API）

```bash
python3 run_test_with_html.py
```

## HTML 表格功能

生成的 HTML 表格包含以下列：

1. **国家** - 固定为"印尼"
2. **学科** - 学科名称（如 Matematika）
3. **年级** - 年级信息（如 Fase A (Kelas 1-2)）
4. **章节** - 章节标题（如 Bilangan, Geometri）
5. **资源类型** - 显示资源类型：
   - 🟢 **播放列表** - YouTube 播放列表
   - 🔵 **频道** - YouTube 频道
   - 🟡 **单集视频（系列）** - 单集视频（可能是系列的一部分）
6. **URL 地址** - 可点击的链接
7. **搜索次数** - 第几次尝试成功
8. **搜索词** - 使用的搜索查询词
9. **理由** - 选择该资源的理由

## 当前问题

### LLM 评估返回空内容

**现象**：LLM API 调用成功，但返回的 `content` 字段为空字符串

**影响**：无法使用 LLM 评估搜索结果质量

**临时解决方案**：
1. 查看示例 HTML 了解表格效果
2. 等待 API 问题解决后重新运行测试

**可能原因**：
- 提示词过长导致 API 限制
- API 临时问题
- 网络连接问题

## 测试数据

测试数据文件：`test_knowledge_points.json`

包含：
- 2 个章节：Bilangan（2个知识点）、Geometri（1个知识点）
- 年级：Fase A (Kelas 1-2)
- 学科：Matematika

## 输出文件

- `test_playlists.csv` - CSV 格式的搜索结果
- `test_playlists.html` - HTML 表格展示

## 下一步

1. ✅ HTML 表格已生成，可以查看效果
2. ⏳ 等待 LLM API 问题解决
3. ⏳ 或实现备用评估方案（基于规则的简单筛选）

