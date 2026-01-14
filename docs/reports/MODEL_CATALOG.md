# 全教育层级智能搜索系统 - 完整模型清单

**版本**: v5.0
**更新日期**: 2026-01-06
**模型总数**: 12个（11个Pydantic模型 + 1个枚举类型）

---

## 📋 目录

1. [核心数据模型](#核心数据模型)
2. [搜索请求模型](#搜索请求模型)
3. [搜索结果模型](#搜索结果模型)
4. [配置模型](#配置模型)
5. [审核系统模型](#审核系统模型)
6. [枚举类型](#枚举类型)
7. [模型关系图](#模型关系图)

---

## 核心数据模型

### 1. CountryProfile 🔵

**文件**: `discovery_agent.py` (Line 39)

**用途**: AI调研生成的国家教育体系完整配置

**字段**:
```python
class CountryProfile(BaseModel):
    """国家教育体系配置"""
    country_code: str                    # 国家代码（ISO 3166-1 alpha-2）
    country_name: str                    # 国家名称（英文）
    country_name_zh: str                 # 国家名称（中文）
    language_code: str                   # 主要语言代码（ISO 639-1）
    grades: List[Dict[str, str]]         # 年级列表（local_name, zh_name）
    subjects: List[Dict[str, str]]       # 核心学科列表（local_name, zh_name）
    grade_subject_mappings: Dict         # 年级-学科配对信息
    domains: List[str]                   # EdTech域名白名单
    notes: str                           # 额外说明
    education_levels: Dict[str, Any]     # 教育层级配置（k12/university/vocational）
```

**特性**:
- ✅ 支持K12、大学、职业三个教育层级
- ✅ 包含年级-学科配对规则
- ✅ 支持多语言（本地语、中文、英语）
- ✅ 可扩展的education_levels字段

**使用场景**: AI自动调研国家教育体系时生成

---

### 2. CountryConfig 🔵

**文件**: `config_manager.py` (Line 18)

**用途**: 配置文件中存储的国家配置（与CountryProfile兼容）

**字段**:
```python
class CountryConfig(BaseModel):
    """国家配置（与 CountryProfile 兼容）"""
    country_code: str
    country_name: str
    country_name_zh: str
    language_code: str
    grades: List[Dict[str, str]]
    subjects: List[Dict[str, str]]
    grade_subject_mappings: Dict[str, Dict[str, Any]]
    domains: List[str]
    notes: str
```

**与CountryProfile的区别**:
- 不包含`education_levels`字段
- 用于向后兼容旧的K12-only配置
- 由ConfigManager管理

**使用场景**: 读写`countries_config.json`文件

---

## 搜索请求模型

### 3. SearchRequest 🟢

**文件**: `search_engine_v2.py` (Line 55)

**用途**: K12教育资源搜索请求

**字段**:
```python
class SearchRequest(BaseModel):
    """搜索请求"""
    country: str                        # 国家代码（如：ID, CN, US）
    grade: str                          # 年级（如：1, 2, 3 或 Kelas 1）
    semester: Optional[str]             # 学期（可选）
    subject: str                        # 学科（如：Matematika, Mathematics）
    language: Optional[str]             # 搜索语言（可选）
```

**使用场景**: K12教育搜索API (`POST /api/search`)

---

### 4. UniversitySearchRequest 🟢

**文件**: `core/university_search_engine.py` (Line 32)

**用途**: 大学教育资源搜索请求

**字段**:
```python
class UniversitySearchRequest(BaseModel):
    """大学教育搜索请求"""
    # 基本信息
    country: str                        # 国家代码
    query: str                          # 搜索查询

    # 大学信息（可选）
    university_code: Optional[str]      # 大学代码（如：UI, ITB）
    faculty_code: Optional[str]         # 学院代码（如：FIK, FT）
    major_code: Optional[str]           # 专业代码（如：TI-SKRI）

    # 课程信息（可选）
    subject_code: Optional[str]         # 课程代码（如：CS101）
    subject_name: Optional[str]         # 课程名称
    year: Optional[int]                 # 学年（1-4）
    semester: Optional[int]             # 学期（1-2）

    # 搜索选项
    max_results: int = 10               # 最大结果数
    domains: List[str]                  # 域名白名单
```

**特性**:
- ✅ 支持4级层级筛选（大学→学院→专业→课程）
- ✅ 所有下级字段都是可选的
- ✅ 支持学年/学期精确筛选

**使用场景**: 大学教育搜索API (`POST /api/search_university`)

---

### 5. VocationalSearchRequest 🟢

**文件**: `core/vocational_search_engine.py` (Line 30)

**用途**: 职业教育搜索请求

**字段**:
```python
class VocationalSearchRequest(BaseModel):
    """职业教育搜索请求"""
    # 基本信息
    country: str                        # 国家代码
    query: str                          # 搜索查询

    # 技能领域信息（可选）
    skill_area: Optional[str]           # 技能领域代码（如：IT, LANG, BIZ）
    program_code: Optional[str]         # 课程代码（如：IT-BASIC）

    # 筛选条件（可选）
    target_audience: Optional[str]      # 目标受众（beginner/advanced等）
    level: Optional[str]                # 技能水平
    provider: Optional[str]             # 培训提供商
    max_duration: Optional[int]         # 最大培训时长（月）
    max_price: Optional[int]            # 最高价格

    # 搜索选项
    max_results: int = 10               # 最大结果数
```

**特性**:
- ✅ 支持多维度筛选（受众、时长、价格）
- ✅ 灵活的目标受众定位
- ✅ 提供商和技能水平筛选

**使用场景**: 职业教育搜索API (`POST /api/search_vocational`)

---

## 搜索结果模型

### 6. SearchResult 🔵

**文件**: `search_engine_v2.py` (Line 64)

**用途**: 单个搜索结果

**字段**:
```python
class SearchResult(BaseModel):
    """单个搜索结果"""
    title: str                          # 搜索结果标题
    url: str                            # 结果URL
    snippet: str                        # 结果摘要
    source: str = "规则"                 # 来源（规则/LLM）
    score: float = 0.0                  # 评估分数（0-10分）
    recommendation_reason: str = ""     # 推荐理由
    resource_type: Optional[str]        # 资源类型（视频、教材等）
    is_selected: bool = False           # 是否被人工选中
    evaluation_status: Optional[str]    # 评估状态
    evaluation_result: Optional[Dict]   # 视频评估结果
```

**特性**:
- ✅ 包含评估分数（0-10分）
- ✅ 支持多种资源类型
- ✅ 可包含视频评估结果

---

### 7. SearchResponse 🔵

**文件**: `search_engine_v2.py` (Line 78)

**用途**: 搜索响应结果

**字段**:
```python
class SearchResponse(BaseModel):
    """搜索响应"""
    success: bool                       # 是否成功
    query: str                          # 使用的搜索词
    results: List[SearchResult]         # 搜索结果列表
    total_count: int = 0                # 结果总数
    playlist_count: int = 0             # 播放列表数量
    video_count: int = 0                # 视频数量
    message: str = ""                   # 消息
    timestamp: str                      # 时间戳（自动生成）
```

**使用场景**: 所有搜索API的响应格式

---

## 配置模型

### 8. UniversityConfig 🔵

**文件**: `core/university_search_engine.py` (Line 54)

**用途**: 大学教育配置文件数据模型

**字段**:
```python
class UniversityConfig(BaseModel):
    """大学配置"""
    country_code: str
    country_name: str
    country_name_zh: str
    education_levels: Dict[str, Any]    # 包含undergraduate配置
```

**education_levels结构**:
```json
{
  "university": {
    "undergraduate": {
      "universities": [
        {
          "university_code": "UI",
          "local_name": "Universitas Indonesia",
          "zh_name": "印度尼西亚大学",
          "faculties": [...]
        }
      ]
    }
  }
}
```

**使用场景**: 加载`indonesia_universities.json`配置

---

### 9. VocationalConfig 🔵

**文件**: `core/vocational_search_engine.py` (Line 51)

**用途**: 职业教育配置文件数据模型

**字段**:
```python
class VocationalConfig(BaseModel):
    """职业教育配置"""
    country_code: str
    country_name: str
    country_name_zh: str
    education_levels: Dict[str, Any]    # 包含vocational配置
```

**education_levels结构**:
```json
{
  "vocational": {
    "skill_areas": [
      {
        "area_code": "IT",
        "icon": "💻",
        "programs": [...]
      }
    ]
  }
}
```

**使用场景**: 加载`indonesia_vocational.json`配置

---

## 审核系统模型

### 10. ReviewRequest 🟡

**文件**: `core/manual_review_system.py` (Line 27)

**用途**: 配置审核请求

**字段**:
```python
class ReviewRequest(BaseModel):
    """审核请求"""
    # 基本信息
    review_id: str                      # 审核ID
    country_code: str                   # 国家代码
    country_name: str                   # 国家名称
    submitter: str                      # 提交人
    submitted_at: str                   # 提交时间
    status: ReviewStatus                # 审核状态

    # 审核内容
    changes: Dict[str, Any]             # 变更内容
    reason: str = ""                    # 提交原因

    # 审核结果
    reviewer: Optional[str]             # 审核人
    reviewed_at: Optional[str]          # 审核时间
    review_comments: Optional[str]      # 审核意见
```

**状态流转**:
```
PENDING → APPROVED
       → REJECTED
       → CHANGES_REQUESTED → PENDING
```

**使用场景**: 配置变更的人工审核流程

---

### 11. ReviewStatistics 🔵

**文件**: `core/manual_review_system.py` (Line 46)

**用途**: 审核统计数据

**字段**:
```python
class ReviewStatistics(BaseModel):
    """审核统计"""
    total_reviews: int                  # 总审核数
    pending_reviews: int                # 待审核数
    approved_reviews: int               # 已通过数
    rejected_reviews: int               # 已拒绝数
    changes_requested_reviews: int      # 需修改数
```

**使用场景**: 管理员查看审核系统统计信息

---

## 枚举类型

### 12. ReviewStatus 🔴

**文件**: `core/manual_review_system.py` (Line 19)

**类型**: `str` Enum

**用途**: 审核状态枚举

**值**:
```python
class ReviewStatus(str, Enum):
    """审核状态"""
    PENDING = "pending"                     # 待审核
    APPROVED = "approved"                   # 已通过
    REJECTED = "rejected"                   # 已拒绝
    CHANGES_REQUESTED = "changes_requested" # 需要修改
```

**状态说明**:
- **PENDING**: 初始状态，等待审核
- **APPROVED**: 审核通过，配置生效
- **REJECTED**: 审核拒绝，配置不生效
- **CHANGES_REQUESTED**: 需要修改，提交人重新提交

---

## 模型关系图

### 数据流关系

```
┌─────────────────────────────────────────────────────────────┐
│                     数据模型关系图                           │
└─────────────────────────────────────────────────────────────┘

[A] 配置数据层
┌──────────────────┐
│  CountryProfile  │──┐
│  CountryConfig   │  │
│  UniversityConfig│  │
│  VocationalConfig│  │
└──────────────────┘  │
                      │
                      ▼
[B] 搜索请求层
┌──────────────────┐
│ SearchRequest    │ (K12)
│ UniversitySearch│ (大学)
│ VocationalSearch │ (职业)
└──────────────────┘
                      │
                      ▼
[C] 搜索结果层
┌──────────────────┐
│  SearchResult    │
│  SearchResponse  │
└──────────────────┘
                      │
                      ▼
[D] 审核系统层
┌──────────────────┐
│  ReviewRequest   │
│  ReviewStatistics│
│  ReviewStatus    │
└──────────────────┘
```

### 模型继承关系

```
BaseModel (Pydantic)
    │
    ├── CountryProfile
    ├── CountryConfig
    ├── SearchRequest
    │   └── (用于K12搜索)
    ├── UniversitySearchRequest
    │   └── (用于大学搜索)
    ├── VocationalSearchRequest
    │   └── (用于职业搜索)
    ├── SearchResult
    ├── SearchResponse
    ├── UniversityConfig
    ├── VocationalConfig
    ├── ReviewRequest
    └── ReviewStatistics

Enum (Python)
    │
    └── ReviewStatus
```

### 教育层级模型映射

```
education_levels 字段结构
│
├── k12 (隐含在grades/subjects字段)
│   ├── grades: List[Dict]
│   ├── subjects: List[Dict]
│   └── grade_subject_mappings: Dict
│
├── university (UniversityConfig)
│   └── undergraduate
│       └── universities
│           ├── faculties
│           │   └── majors
│           │       └── subjects
│
└── vocational (VocationalConfig)
    └── skill_areas
        └── programs
            └── skills
```

---

## 模型使用场景

### 场景1: K12教育搜索

```python
# 1. 加载国家配置
config = ConfigManager()
country = config.get_country_config("ID")  # → CountryConfig

# 2. 验证年级-学科配对
validator = GradeSubjectValidator()
result = validator.validate("ID", "Kelas 1", "Matematika")

# 3. 创建搜索请求
request = SearchRequest(
    country="ID",
    grade="Kelas 1",
    subject="Matematika",
    query="Pecahan"
)

# 4. 执行搜索
response = SearchEngineV2().search(request)  # → SearchResponse
```

### 场景2: 大学教育搜索

```python
# 1. 加载大学配置
engine = UniversitySearchEngine()  # → UniversityConfig

# 2. 获取大学列表
universities = engine.get_available_universities("ID")

# 3. 创建搜索请求
request = UniversitySearchRequest(
    country="ID",
    query="Algoritma",
    university_code="UI",
    faculty_code="FIK",
    major_code="TI-SKRI"
)

# 4. 执行搜索
response = engine.search(request)  # → SearchResponse
```

### 场景3: 职业教育搜索

```python
# 1. 加载职业配置
engine = VocationalSearchEngine()  # → VocationalConfig

# 2. 获取技能领域
areas = engine.get_available_skill_areas("ID")

# 3. 创建搜索请求
request = VocationalSearchRequest(
    country="ID",
    query="Python",
    skill_area="IT",
    target_audience="advanced"
)

# 4. 执行搜索
response = engine.search(request)  # → SearchResponse
```

### 场景4: 配置审核

```python
# 1. 提交审核
system = ManualReviewSystem()
review_id = system.submit_for_review(
    country_code="SG",
    country_name="Singapore",
    changes={...},
    submitter="admin"
)  # → 创建 ReviewRequest

# 2. 审核流程
request = system.get_review_request(review_id)  # → ReviewRequest
system.approve_review(review_id, reviewer="admin")  # 更新状态

# 3. 查看统计
stats = system.get_statistics()  # → ReviewStatistics
```

---

## 模型验证规则

### Pydantic验证特性

所有模型都使用Pydantic v2进行数据验证：

1. **类型验证**: 自动检查字段类型
2. **必填字段**: 未提供默认值的字段为必填
3. **可选字段**: `Optional[T]`或提供默认值的字段
4. **描述字段**: 使用`Field(description=...)`添加文档
5. **默认值**: 使用`default`或`default_factory`设置

### 示例验证

```python
# ✅ 有效请求
request = UniversitySearchRequest(
    country="ID",  # 必填
    query="Algoritma",  # 必填
    university_code="UI",  # 可选
    max_results=10  # 有默认值
)

# ❌ 无效请求 - 缺少必填字段
request = UniversitySearchRequest(
    # country缺失 - 会抛出ValidationError
    query="Algoritma"
)

# ✅ 最小有效请求
request = UniversitySearchRequest(
    country="ID",
    query="Algoritma"
)
```

---

## 模型扩展性

### 添加新字段示例

```python
class CountryProfile(BaseModel):
    # ... 现有字段 ...

    # 新增字段示例
    region: Optional[str] = Field(
        description="地理区域（如：Southeast Asia）",
        default=None
    )

    population: Optional[int] = Field(
        description="国家人口",
        default=None
    )

    # 完全向后兼容！
```

### 添加新教育层级

```python
# 1. 扩展education_levels字段
education_levels: Dict[str, Any] = Field(
    description="教育层级配置",
    default_factory=dict
)

# 2. 添加新层级配置
education_levels = {
    "k12": {...},
    "university": {...},
    "vocational": {...},
    "postgraduate": {  # 新层级！
        "masters": {...},
        "doctoral": {...}
    }
}

# 3. 创建新的搜索请求模型
class PostgraduateSearchRequest(BaseModel):
    country: str
    query: str
    degree_type: Optional[str]  # masters/doctoral
    # ...
```

---

## 模型最佳实践

### 1. 使用类型注解

```python
# ✅ 推荐
grades: List[Dict[str, str]]

# ❌ 不推荐
grades: list
```

### 2. 提供描述信息

```python
# ✅ 推荐
country_code: str = Field(description="国家代码（ISO 3166-1 alpha-2）")

# ❌ 不推荐
country_code: str
```

### 3. 使用Optional表示可选字段

```python
# ✅ 推荐
university_code: Optional[str] = Field(default=None)

# ❌ 不推荐
university_code: str = None
```

### 4. 使用default_factory处理可变默认值

```python
# ✅ 推荐
grades: List[Dict[str, str]] = Field(default_factory=list)

# ❌ 不推荐
grades: List[Dict[str, str]] = []
```

---

## 总结

### 模型分类统计

| 类别 | 数量 | 模型列表 |
|------|------|---------|
| **核心数据模型** | 2个 | CountryProfile, CountryConfig |
| **搜索请求模型** | 3个 | SearchRequest, UniversitySearchRequest, VocationalSearchRequest |
| **搜索结果模型** | 2个 | SearchResult, SearchResponse |
| **配置模型** | 2个 | UniversityConfig, VocationalConfig |
| **审核系统模型** | 2个 | ReviewRequest, ReviewStatistics |
| **枚举类型** | 1个 | ReviewStatus |
| **总计** | **12个** | - |

### 核心特性

- ✅ **类型安全**: 使用Pydantic v2严格类型检查
- ✅ **自动验证**: 输入数据自动验证
- ✅ **文档化**: 每个字段都有描述信息
- ✅ **向后兼容**: 所有新字段都提供默认值
- ✅ **可扩展**: 易于添加新字段和新教育层级
- ✅ **多语言支持**: 支持本地语、中文、英语

### 使用建议

1. **优先使用SearchRequest系列模型**进行API调用
2. **使用Config系列模型**加载配置文件
3. **ReviewRequest模型**用于审核系统
4. **所有模型都是独立的**，可以单独使用

---

**文档版本**: v1.0
**最后更新**: 2026-01-06
**维护团队**: Education Search System Dev Team
