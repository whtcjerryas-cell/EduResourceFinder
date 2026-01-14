#!/usr/bin/env python3
"""
日志工具模块 - 统一管理日志输出
同时输出到控制台和文件
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone

# 日志文件路径
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(LOG_DIR, 'search_system.log')

# 全局日志记录器
_logger = None


# 存储所有已创建的logger，避免重复创建处理器
_loggers = {}

def get_logger(name: str = 'search_system', log_file: str = None) -> logging.Logger:
    """
    获取日志记录器
    
    修复：每个模块使用独立的logger名称，避免共享全局_logger导致命名混乱
    
    Args:
        name: 日志记录器名称（重要：每个模块应该使用唯一的名称）
        log_file: 日志文件路径，如果为 None 则使用默认路径
    
    Returns:
        logging.Logger 实例
    """
    # 如果已经创建过该名称的logger，直接返回
    if name in _loggers:
        return _loggers[name]
    
    log_file_path = log_file or LOG_FILE
    
    # 创建日志记录器（使用指定的name）
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加处理器（如果logger已经有处理器，说明已经配置过）
    if logger.handlers:
        _loggers[name] = logger
        return logger
    
    # 日志格式（包含logger名称，便于区分）
    # 使用 UTC 时间，避免时区混乱
    import time as time_module
    class UTCFormatter(logging.Formatter):
        """UTC 时区的日志格式化器"""
        def formatTime(self, record, datefmt=None):
            utc_time = datetime.fromtimestamp(record.created, tz=timezone.utc)
            if datefmt:
                return utc_time.strftime(datefmt)
            # 使用ISO 8601格式，与前端保持一致
            return utc_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = None  # 使用默认的ISO格式
    formatter_class = UTCFormatter
    
    # 文件日志处理器（轮转，最大10MB，保留5个备份）
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter_class(log_format, date_format))
    
    # 控制台日志处理器（详细模式：显示所有DEBUG及以上级别）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)  # 控制台显示所有级别（DEBUG, INFO, WARNING, ERROR）
    console_handler.setFormatter(formatter_class(log_format, date_format))
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 防止logger向上传播（避免重复日志）
    logger.propagate = False
    
    # 缓存logger
    _loggers[name] = logger
    
    # 只在第一次创建时记录日志系统启动（使用第一个logger）
    if len(_loggers) == 1:
        logger.info("="*80)
        logger.info(f"📝 日志系统启动 - 日志文件: {log_file_path}")
        logger.info("="*80)
    
    return logger


def log_print(message: str, level: str = 'INFO'):
    """
    打印日志（同时输出到控制台和文件）
    
    Args:
        message: 日志消息
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger = get_logger()
    
    # 移除消息中的 emoji 和特殊字符，保留纯文本用于日志文件
    # 但控制台输出保持原样（通过 logger 的格式化）
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.log(log_level, message)


# 便捷函数
def debug(msg: str):
    """DEBUG 级别日志"""
    log_print(msg, 'DEBUG')


def info(msg: str):
    """INFO 级别日志"""
    log_print(msg, 'INFO')


def warning(msg: str):
    """WARNING 级别日志"""
    log_print(msg, 'WARNING')


def error(msg: str):
    """ERROR 级别日志"""
    log_print(msg, 'ERROR')


def critical(msg: str):
    """CRITICAL 级别日志"""
    log_print(msg, 'CRITICAL')


# 兼容 print 的函数（用于替换 print 语句）
def print_log(*args, sep=' ', end='\n', level='INFO'):
    """
    兼容 print 的日志函数
    
    Args:
        *args: 要打印的参数
        sep: 分隔符
        end: 结束符
        level: 日志级别
    """
    message = sep.join(str(arg) for arg in args) + end.rstrip('\n')
    log_print(message, level)


# 重定向 print 到日志（可选）
class PrintToLog:
    """将 print 重定向到日志的上下文管理器"""
    
    def __init__(self, level='INFO'):
        self.level = level
        self.original_print = __builtins__['print']
        self.logger = get_logger()
    
    def __enter__(self):
        def print_to_log(*args, sep=' ', end='\n', file=None, flush=False):
            if file is None or file == sys.stdout:
                message = sep.join(str(arg) for arg in args) + end.rstrip('\n')
                log_level = getattr(logging, self.level.upper(), logging.INFO)
                self.logger.log(log_level, message)
            else:
                self.original_print(*args, sep=sep, end=end, file=file, flush=flush)
        
        __builtins__['print'] = print_to_log
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        __builtins__['print'] = self.original_print
        return False


if __name__ == '__main__':
    # 测试日志功能
    logger = get_logger('test')
    logger.info("测试日志功能")
    logger.debug("这是 DEBUG 级别（只写入文件）")
    logger.info("这是 INFO 级别（控制台和文件）")
    logger.warning("这是 WARNING 级别")
    logger.error("这是 ERROR 级别")
    
    print(f"\n✅ 日志文件位置: {LOG_FILE}")
    print(f"✅ 请检查文件: {os.path.abspath(LOG_FILE)}")

