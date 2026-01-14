#!/usr/bin/env python3
"""
常量配置 - 集中管理魔法数字和配置值
"""


# ============================================================================
# 搜索相关配置
# ============================================================================

# 默认搜索结果数量
DEFAULT_MAX_RESULTS = 10
MIN_RESULTS = 1
MAX_RESULTS = 50

# 搜索超时配置
SEARCH_TIMEOUT_SECONDS = 150  # 总搜索超时
API_REQUEST_TIMEOUT = 10  # API请求默认超时
SMART_SEARCH_TIMEOUT = 60  # 智能搜索超时

# 并发搜索配置
MAX_PARALLEL_SEARCHES = 5  # 最大并行搜索数
DEFAULT_PARALLEL_WORKERS = 3  # 默认并行工作线程数

# 并发限制
CONCURRENCY_LIMITER_TIMEOUT = 5.0  # 并发限制器获取超时


# ============================================================================
# Excel导出配置
# ============================================================================

# Excel列宽配置
EXCEL_COLUMN_WIDTHS = {
    'A': 6,   # 序号
    'B': 12,  # 国家
    'C': 12,  # 年级
    'D': 12,  # 学科
    'E': 50,  # 标题
    'F': 60,  # URL
    'G': 80,  # 摘要
    'H': 12,  # 资源类型
    'I': 10,  # 质量分数
    'J': 40,  # 推荐理由
    'K': 15,  # 来源
    'L': 12,  # 视频数量
    'M': 15,  # 总时长(分钟)
}

# Excel行高
EXCEL_HEADER_ROW_HEIGHT = 30
EXCEL_DATA_ROW_HEIGHT = 60

# Excel批处理大小（用于处理大量数据）
EXCEL_BATCH_SIZE = 1000


# ============================================================================
# 日志和监控配置
# ============================================================================

# Request ID长度
REQUEST_ID_LENGTH = 8

# 日志级别
LOG_LEVEL_DEBUG = 'DEBUG'
LOG_LEVEL_INFO = 'INFO'
LOG_LEVEL_WARNING = 'WARNING'
LOG_LEVEL_ERROR = 'ERROR'


# ============================================================================
# API响应配置
# ============================================================================

# HTTP状态码
HTTP_SUCCESS = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404
HTTP_SERVER_ERROR = 500
HTTP_SERVICE_UNAVAILABLE = 503


# ============================================================================
# 资源类型
# ============================================================================

RESOURCE_TYPE_ALL = 'all'
RESOURCE_TYPE_PLAYLIST = 'playlist'
RESOURCE_TYPE_VIDEO = 'video'
RESOURCE_TYPE_TEXTBOOK = 'textbook'
RESOURCE_TYPE_OTHER = 'other'

RESOURCE_TYPES = [
    RESOURCE_TYPE_ALL,
    RESOURCE_TYPE_PLAYLIST,
    RESOURCE_TYPE_VIDEO,
    RESOURCE_TYPE_TEXTBOOK,
    RESOURCE_TYPE_OTHER
]


# ============================================================================
# 评分配置
# ============================================================================

# 评分范围
MIN_SCORE = 0.0
MAX_SCORE = 10.0
DEFAULT_SCORE = 5.0

# 高质量阈值
HIGH_QUALITY_THRESHOLD = 7.0
LOW_QUALITY_THRESHOLD = 4.0


# ============================================================================
# 文件路径配置
# ============================================================================

# 导出文件目录
EXPORT_DIR = 'exports'

# 日志目录
LOG_DIR = 'logs'

# 配置文件目录
CONFIG_DIR = 'config'
DATA_DIR = 'data'


# ============================================================================
# 视频处理配置
# ============================================================================

# 视频信息获取超时
VIDEO_INFO_TIMEOUT = 30

# 播放列表最大视频数（避免过长时间）
MAX_PLAYLIST_VIDEOS = 200


# ============================================================================
# 缓存配置
# ============================================================================

# 搜索结果缓存时间（秒）
SEARCH_CACHE_TTL = 3600  # 1小时

# 配置缓存时间（秒）
CONFIG_CACHE_TTL = 7200  # 2小时
