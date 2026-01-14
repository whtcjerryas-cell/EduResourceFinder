# 伊拉克搜索修复方案 - 测试指南

## 实施完成情况

✅ **已完成**:
1. 创建了 `core/intelligent_query_generator.py` - 基于LLM的智能查询生成器
2. 集成到 `search_engine_v2.py` - 在搜索流程中优先使用智能生成器
3. 设计了优化的LLM提示词，支持多语言智能识别

## 测试方法

### 方法1: 使用Web API测试（推荐）

启动服务器后，使用curl或Postman测试：

#### 测试1: 伊拉克数学搜索

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "country": "伊拉克",
    "grade": "三年级",
    "subject": "数学"
  }'
```

**预期结果**:
- ✅ 搜索词应该包含阿拉伯语（如："الرياضيات الصف الثالث"）
- ✅ 搜索结果应该是阿拉伯语教育资源，而不是中文资源

#### 测试2: 印尼自然科学搜索

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "country": "印尼",
    "grade": "七年级",
    "subject": "自然科学"
  }'
```

**预期结果**:
- ✅ 搜索词应该包含印尼语（如："IPA Kelas 7"）
- ✅ 搜索结果应该是印尼语教育资源

#### 测试3: 中国数学搜索（向后兼容）

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "country": "中国",
    "grade": "五年级",
    "subject": "数学"
  }'
```

**预期结果**:
- ✅ 搜索词应该是中文（如："五年级数学 播放列表"）
- ✅ 搜索结果应该是中文教育资源
- ✅ 确保中国搜索不受影响（向后兼容）

## 验证标准

### ✅ 成功标志

1. **伊拉克搜索**
   - 搜索词包含阿拉伯语字符
   - 搜索结果不是中文内容
   - 结果包含阿拉伯语教育资源

2. **印尼搜索**
   - 搜索词包含印尼语特征（kelas, IPA等）
   - 搜索结果包含印尼语教育资源

3. **中国搜索**
   - 搜索词保持中文
   - 搜索结果保持中文
   - 无任何副作用

4. **灵活性**
   - 支持中文输入（"伊拉克"）
   - 支持国家代码（"IQ"）
   - 支持英文国家名（"Iraq"）

## 下一步

请在配置好的环境中测试以上场景，并根据实际结果调整LLM prompt。
