# P1 代码质量改进实施计划

## 概述

本文档详细说明了 `llm_client.py` 中 P1 优先级任务的实施计划。这些任务需要 29-43 小时的工作量。

## ✅ 已完成（P0 关键安全问题）

### 1. SSL 证书验证修复
- **位置**: Line 338
- **修改**: `verify=False` → `verify=True`
- **影响**: 消除中间人攻击风险

### 2. 路径遍历漏洞修复
- **位置**: Lines 387-483
- **修改**:
  - 添加路径白名单验证
  - 限制文件访问目录
  - 文件类型和大小验证
- **影响**: 阻止任意文件读取

### 3. 敏感信息泄露修复
- **位置**: Lines 203-207, 660-664
- **修改**: 移除 prompt 内容打印
- **影响**: 保护用户隐私数据

---

## 📋 待实施 P1 任务

### P1-1: 重构 search() 方法降低圈复杂度（8-12小时）

**当前状态**:
- 方法长度: 104行
- 圈复杂度: >15
- 嵌套层级: 5层
- 职责数量: 5+种

**目标**:
- 方法长度: <30行
- 圈复杂度: <5
- 嵌套层级: <3层
- 符合开闭原则

**推荐方案**: 策略模式重构

```python
# 1. 创建策略接口
class SearchStrategy(ABC):
    @abstractmethod
    def can_handle(self, query: str, context: SearchContext) -> bool:
        pass

    @abstractmethod
    def search(self, query: str, max_results: int, include_domains: Optional[List[str]]) -> List[Dict]:
        pass

# 2. 实现具体策略
class ChineseGoogleStrategy(SearchStrategy):
    """中文内容优先使用Google"""

class EnglishGoogleStrategy(SearchStrategy):
    """英语内容优先使用Google"""

class DefaultTavilyStrategy(SearchStrategy):
    """默认使用Tavily"""

# 3. 创建编排器
class SearchOrchestrator:
    def __init__(self):
        self.strategies = [
            ChineseGoogleStrategy(),
            EnglishGoogleStrategy(),
            DefaultTavilyStrategy(),
        ]

    def search(self, query, max_results, include_domains, context):
        for strategy in self.strategies:
            if strategy.can_handle(query, context):
                return strategy.search(query, max_results, include_domains)
```

**实施步骤**:
1. 创建 `llm/strategies/` 目录结构
2. 定义抽象基类
3. 实现 5-7 个具体策略类
4. 编写单元测试
5. 替换现有 search() 方法
6. 集成测试

---

### P1-2: 添加单元测试（16-24小时）

**当前状态**: 测试覆盖率 <10%

**目标**: 测试覆盖率 >80%

**需要测试的核心方法**:
1. `InternalAPIClient.call_llm()`
2. `InternalAPIClient.call_llm_async()`
3. `InternalAPIClient._image_to_base64()`
4. `InternalAPIClient.call_with_vision()`
5. `AIBuildersAPIClient.call_llm()`
6. `UnifiedLLMClient.search()`
7. 路径验证逻辑

**测试框架**: pytest

**示例测试**:

```python
# tests/test_llm_client.py
import pytest
from pathlib import Path
from llm_client import InternalAPIClient

class TestInternalAPIClient:
    def test_init_with_api_key(self):
        client = InternalAPIClient(api_key="test_key")
        assert client.api_key == "test_key"

    def test_init_without_api_key_raises_error(self):
        with pytest.raises(ValueError):
            InternalAPIClient()

    def test_image_to_base64_valid_image(self):
        client = InternalAPIClient(api_key="test_key")
        # 创建测试图片
        test_image = Path("data/images/test.jpg")
        result = client._image_to_base64(str(test_image))
        assert result.startswith("data:image/jpeg;base64,")

    def test_image_to_base64_path_traversal_attack(self):
        client = InternalAPIClient(api_key="test_key")
        with pytest.raises(ValueError, match="不在允许的目录内"):
            client._image_to_base64("../../../etc/passwd")

    def test_image_to_base64_invalid_extension(self):
        client = InternalAPIClient(api_key="test_key")
        test_file = Path("data/images/test.txt")
        with pytest.raises(ValueError, match="不允许的文件类型"):
            client._image_to_base64(str(test_file))
```

**实施步骤**:
1. 创建 `tests/` 目录
2. 设置 pytest 配置
3. 为每个类编写测试文件
4. 添加 mock 和 fixture
5. 实现 CI 集成

---

### P1-3: 消除配置加载重复（2-3小时）

**当前问题**: 配置加载代码在 3 处重复

**重复位置**:
1. `InternalAPIClient.call_llm()` - Lines 174-180
2. `InternalAPIClient.call_llm_async()` - Lines 295-301
3. `InternalAPIClient.call_with_vision()` - Lines 445-451

**解决方案**: 提取为辅助方法

```python
def _get_llm_params(self, param_type: str = 'default') -> tuple:
    """
    获取 LLM 参数（统一方法）

    Args:
        param_type: 参数类型 ('default' 或 'vision')

    Returns:
        (max_tokens, temperature) 元组
    """
    config = get_config()
    params = config.get_llm_params(param_type)
    max_tokens = params.get('max_tokens', 8000)
    temperature = params.get('temperature', 0.3)
    return max_tokens, temperature
```

**实施步骤**:
1. 提取 `_get_llm_params()` 方法
2. 替换 3 处重复代码
3. 测试确保功能一致

---

### P1-4: 使用 logger 替代 print（3-4小时）

**当前问题**: 100+ 处 print 语句

**影响**:
- 无法控制日志级别
- 无法输出到文件
- 无法结构化日志
- 生产环境调试困难

**解决方案**: 逐步迁移到 logger

```python
# 替换前
print(f"[🔍 搜索] 使用 Google")

# 替换后
logger.info(f"使用 Google 搜索", extra={"search_engine": "Google"})
```

**实施步骤**:
1. 定义日志级别规范
2. 替换错误日志 → logger.error()
3. 替换警告日志 → logger.warning()
4. 替换信息日志 → logger.info()
5. 替换调试日志 → logger.debug()
6. 配置日志输出格式

**日志级别规范**:
- ERROR: API 调用失败、文件读取错误
- WARNING: 降级到备用 API、额度不足
- INFO: 正常操作（搜索、API 调用）
- DEBUG: 详细参数、响应内容

---

## 🎯 优先级建议

### 第 1 周 (最简单快速)
1. ✅ P0-1: SSL 验证修复（已完成）
2. ✅ P0-2: 路径遍历修复（已完成）
3. ✅ P0-3: 敏感信息修复（已完成）
4. 🔄 P1-3: 消除配置重复（2-3小时）← 立即可做

### 第 2-3 周（中等复杂度）
5. 📋 P1-4: Logger 替换 print（3-4小时）
6. 📋 P1-2: 添加单元测试（16-24小时）

### 第 4-6 周（复杂重构）
7. 📋 P1-1: search() 方法重构（8-12小时）

---

## 🚀 快速开始

如果您想继续实施 P1 任务，建议按以下顺序：

```bash
# 1. 先做最简单的 P1-3（消除配置重复）
# 只需修改 3 处代码，30 分钟完成

# 2. 然后逐步添加测试（P1-2）
# 从最重要的方法开始测试

# 3. 最后重构 search() 方法（P1-1）
# 这需要最多的时间
```

---

## 📊 预期改进

实施所有 P0 + P1 修复后:

| 指标 | 当前值 | 目标值 | 改进 |
|------|--------|--------|------|
| 安全漏洞 | 8个 → | 0个 | ✅ P0 已完成 |
| 代码复杂度 | >15 → | <5 | 🔄 P1-1 待完成 |
| 测试覆盖率 | <10% → | >80% | 📋 P1-2 待完成 |
| 代码重复 | 20% → | <5% | 📋 P1-3 待完成 |
| 日志规范 | print → | logger | 📋 P1-4 待完成 |

---

## 📝 实施记录

### 2026-01-21
- ✅ P0-1: SSL 证书验证修复完成
- ✅ P0-2: 路径遍历漏洞修复完成
- ✅ P0-3: 敏感信息泄露修复完成
- 📋 创建 P1 实施计划

### 下一步
- [ ] P1-3: 消除配置加载重复
- [ ] P1-2: 添加单元测试
- [ ] P1-4: Logger 替换 print
- [ ] P1-1: search() 方法重构

---

**文档创建日期**: 2026-01-21
**最后更新**: 2026-01-21
**状态**: P0 完成，P1 规划中
