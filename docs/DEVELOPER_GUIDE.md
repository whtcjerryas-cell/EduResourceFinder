# 教育搜索系统 - 开发者指南

**版本**: v5.0 (全教育层级支持)
**更新日期**: 2026-01-06
**技术栈**: Python 3.9+, Flask, Pydantic

---

## 📚 目录

1. [系统架构](#系统架构)
2. [开发环境搭建](#开发环境搭建)
3. [核心模块说明](#核心模块说明)
4. [API开发指南](#api开发指南)
5. [数据模型](#数据模型)
6. [测试指南](#测试指南)
7. [部署指南](#部署指南)

---

## 系统架构

### 整体架构

```
┌─────────────────────────────────────────────┐
│              Web Layer (Flask)               │
│  web_app.py (3183 lines)                    │
│  - K12 Search API                           │
│  - University Search API                    │
│  - Vocational Search API                    │
│  - Manual Review API                        │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│           Business Logic Layer              │
│  ┌─────────────────────────────────────┐   │
│  │ Core Modules                          │   │
│  │ - grade_subject_validator.py         │   │
│  │ - university_search_engine.py         │   │
│  │ - vocational_search_engine.py         │   │
│  │ - manual_review_system.py            │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │ Search Engines                        │   │
│  │ - search_engine_v2.py                │   │
│  │ - discovery_agent.py                  │   │
│  └─────────────────────────────────────┘   │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│            Data Layer                       │
│  ┌─────────────────────────────────────┐   │
│  │ Configuration Files                   │   │
│  │ - countries_config.json              │   │
│  │ - grade_subject_rules.json          │   │
│  │ - indonesia_universities.json        │   │
│  │ - indonesia_vocational.json         │   │
│  │ - review_requests.json               │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### 技术栈

- **Web框架**: Flask 3.x
- **数据验证**: Pydantic v2
- **搜索引擎**: Tavily + AI Builders API
- **日志**: Python logging
- **测试**: pytest (单元测试), 自定义测试框架

---

## 开发环境搭建

### 1. 克隆仓库

```bash
git clone <repository-url>
cd Indonesia
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate   # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖:
- Flask >= 3.0
- Pydantic >= 2.0
- Requests >= 2.31
- python-dotenv >= 1.0.0

### 4. 配置环境变量

创建 `.env` 文件:

```bash
# AI Builders API
AIBUILDERS_API_KEY=your_api_key_here

# 搜索引擎配置
MAX_RESULTS=10
SEARCH_TIMEOUT=30

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=search_system.log
```

### 5. 运行开发服务器

```bash
python3 web_app.py
```

服务将在 `http://localhost:5001` 启动。

---

## 核心模块说明

### 1. 配置管理 (config_manager.py)

**功能**: 管理国家配置数据

**主要类**:
```python
class ConfigManager:
    def get_country_config(country_code) -> CountryConfig
    def update_country_config(profile: CountryProfile)
    def get_all_countries() -> List[Dict]
    def delete_country_config(country_code) -> bool
```

**使用示例**:
```python
from config_manager import ConfigManager

manager = ConfigManager()

# 获取国家配置
config = manager.get_country_config("ID")

# 更新配置
manager.update_country_config(profile)

# 获取所有国家
countries = manager.get_all_countries()
```

### 2. 年级-学科验证器 (core/grade_subject_validator.py)

**功能**: 验证年级-学科配对是否合法

**主要方法**:
```python
class GradeSubjectValidator:
    def validate(country_code, grade, subject) -> Dict
    def get_available_subjects(country_code, grade, subjects) -> List
    def get_streams_for_grade(country_code, grade) -> List
```

**使用示例**:
```python
from core.grade_subject_validator import GradeSubjectValidator

validator = GradeSubjectValidator()

# 验证配对
result = validator.validate("ID", "Kelas 1", "Fisika")
# {'valid': False, 'reason': '1-2年级不开设物理化学'}

# 获取可用学科
subjects = validator.get_available_subjects("ID", "Kelas 1", all_subjects)
```

### 3. 大学搜索引擎 (core/university_search_engine.py)

**功能**: 搜索大学教育资源

**主要方法**:
```python
class UniversitySearchEngine:
    def search(request: UniversitySearchRequest) -> Dict
    def get_available_universities(country_code) -> List
    def get_available_faculties(country_code, uni_code) -> List
    def get_available_majors(country_code, uni_code, fac_code) -> List
    def get_available_subjects(country_code, uni_code, fac_code, maj_code) -> List
```

**使用示例**:
```python
from core.university_search_engine import UniversitySearchEngine, UniversitySearchRequest

engine = UniversitySearchEngine()

# 搜索课程
request = UniversitySearchRequest(
    country="ID",
    query="Algoritma",
    university_code="UI",
    faculty_code="FIK"
)

results = engine.search(request)
```

### 4. 职业搜索引擎 (core/vocational_search_engine.py)

**功能**: 搜索职业教育资源

**主要方法**:
```python
class VocationalSearchEngine:
    def search(request: VocationalSearchRequest) -> Dict
    def get_available_skill_areas(country_code) -> List
    def get_available_programs(country_code, skill_area, filters) -> List
    def get_program_skills(country_code, skill_area, program_code) -> List
```

**使用示例**:
```python
from core.vocational_search_engine import VocationalSearchEngine, VocationalSearchRequest

engine = VocationalSearchEngine()

# 搜索课程
request = VocationalSearchRequest(
    country="ID",
    query="Python",
    skill_area="IT",
    target_audience="advanced"
)

results = engine.search(request)
```

### 5. 人工审核系统 (core/manual_review_system.py)

**功能**: 管理配置审核流程

**主要方法**:
```python
class ManualReviewSystem:
    def submit_for_review(...) -> str
    def approve_review(review_id, reviewer, comments) -> bool
    def reject_review(review_id, reviewer, reason) -> bool
    def list_review_requests(status, country_code) -> List
    def get_statistics() -> ReviewStatistics
```

---

## API开发指南

### 添加新的API端点

在 `web_app.py` 中添加新路由:

```python
@app.route('/api/your_endpoint', methods=['POST'])
def your_endpoint():
    """API文档"""
    try:
        data = request.get_json()

        # 验证输入
        if not data.get('required_field'):
            return jsonify({
                "success": False,
                "message": "缺少必填字段"
            }), 400

        # 处理逻辑
        result = process_data(data)

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"处理失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
```

### 错误处理最佳实践

1. **使用Pydantic验证输入**
```python
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    country: str = Field(..., min_length=2, max_length=2)
    query: str = Field(..., min_length=1)
    max_results: int = Field(default=10, ge=1, le=100)
```

2. **统一错误响应格式**
```python
{
    "success": False,
    "message": "错误描述",
    "error_code": "ERROR_CODE"
}
```

3. **记录详细日志**
```python
logger.error(f"API调用失败: endpoint={endpoint}, error={str(e)}")
```

---

## 数据模型

### CountryProfile (discovery_agent.py)

K12国家教育体系配置:

```python
class CountryProfile(BaseModel):
    country_code: str                    # 国家代码
    country_name: str                    # 国家名称（英文）
    country_name_zh: str                # 国家名称（中文）
    language_code: str                  # 语言代码
    grades: List[Dict[str, str]]         # 年级列表
    subjects: List[Dict[str, str]]       # 学科列表
    grade_subject_mappings: Dict        # 年级-学科配对
    domains: List[str]                   # 域名白名单
    notes: str                           # 说明
    education_levels: Dict               # 教育层级配置
```

### UniversitySearchRequest (core/university_search_engine.py)

大学搜索请求:

```python
class UniversitySearchRequest(BaseModel):
    country: str                         # 国家代码
    query: str                           # 搜索查询
    university_code: Optional[str]       # 大学代码
    faculty_code: Optional[str]          # 学院代码
    major_code: Optional[str]            # 专业代码
    subject_code: Optional[str]          # 课程代码
    year: Optional[int]                  # 学年
    semester: Optional[int]              # 学期
    max_results: int = 10                # 最大结果数
```

### VocationalSearchRequest (core/vocational_search_engine.py)

职业教育搜索请求:

```python
class VocationalSearchRequest(BaseModel):
    country: str                         # 国家代码
    query: str                           # 搜索查询
    skill_area: Optional[str]            # 技能领域
    program_code: Optional[str]          # 课程代码
    target_audience: Optional[str]       # 目标受众
    level: Optional[str]                 # 技能水平
    provider: Optional[str]              # 提供商
    max_duration: Optional[int]          # 最大时长
    max_price: Optional[int]             # 最高价格
    max_results: int = 10                # 最大结果数
```

---

## 测试指南

### 运行所有测试

```bash
# 自动化测试
python3 run_all_tests.py

# 综合系统测试
python3 tests/test_comprehensive_system.py
```

### 编写单元测试

在 `tests/` 目录下创建测试文件:

```python
# tests/test_your_module.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from your_module import YourClass

def test_your_function():
    """测试函数"""
    obj = YourClass()
    result = obj.your_method()
    assert result == expected_value
    print(f"✅ 测试通过")
    return True

if __name__ == "__main__":
    test_your_function()
```

### 运行单个测试

```bash
python3 tests/test_your_module.py
```

---

## 部署指南

### 生产环境部署

#### 1. 使用Gunicorn

```bash
# 安装gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -b 0.0.0.0:5001 web_app:app
```

#### 2. 使用Systemd服务

创建 `/etc/systemd/system/education-search.service`:

```ini
[Unit]
Description=Education Search System
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/Indonesia
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:5001 web_app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl start education-search
sudo systemctl enable education-search
```

### Docker部署

创建 `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "web_app:app"]
```

构建和运行:
```bash
docker build -t education-search .
docker run -p 5001:5001 education-search
```

---

## 扩展开发指南

### 添加新的教育层级

1. **创建配置文件**
   - 在 `data/config/` 下创建配置
   - 使用JSON格式

2. **实现搜索引擎**
   - 继承通用搜索引擎模式
   - 实现特定层级的方法

3. **添加API端点**
   - 在 `web_app.py` 中添加路由
   - 遵循RESTful设计

### 添加新的国家

1. **自动发现**
```python
from discovery_agent import CountryDiscoveryAgent

agent = CountryDiscoveryAgent()
profile = agent.discover_country_profile("Singapore")
```

2. **人工配置**
```python
from config_manager import ConfigManager
from discovery_agent import CountryProfile

config = ConfigManager()
profile = CountryProfile(
    country_code="SG",
    country_name="Singapore",
    # ... 其他字段
)
config.update_country_config(profile)
```

---

## 性能优化建议

### 1. 缓存策略

- 使用Redis缓存搜索结果
- 缓存国家配置数据
- 缓存大学/职业课程数据

### 2. 数据库优化

- 考虑使用PostgreSQL替代JSON文件
- 为常用查询添加索引
- 实现数据库连接池

### 3. 异步处理

- 使用Celery处理长时间任务
- 实现后台搜索队列
- WebSocket推送结果

---

## 故障排查

### 常见问题

**1. 模块导入错误**
```bash
# 解决方案: 确保在项目根目录运行
cd /path/to/Indonesia
export PYTHONPATH=/path/to/Indonesia:$PYTHONPATH
```

**2. API调用失败**
```bash
# 检查环境变量
cat .env

# 检查日志
tail -f search_system.log
```

**3. 端口被占用**
```bash
# 查找占用进程
lsof -i :5001

# 杀死进程
kill -9 <PID>
```

---

## 贡献指南

### 代码规范

- 遵循PEP 8
- 使用类型注解
- 编写docstring
- 添加单元测试

### 提交流程

1. Fork仓库
2. 创建feature分支
3. 提交代码
4. 创建Pull Request
5. 代码审查
6. 合并到主分支

---

**文档版本**: v5.0
**最后更新**: 2026-01-06
**维护团队**: Education Search System Dev Team
