#!/usr/bin/env python3
"""
配置管理器 - 管理 countries_config.json
负责读取和写入国家配置信息
"""

import os
import json
from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field
from tools.discovery_agent import CountryProfile

# ✅ 安全修复：导入安全文件操作模块（Issue #040: Path Traversal - FIXED）
from core.file_utils import safe_read_json, safe_write_json, safe_path_join


# ============================================================================
# 数据模型
# ============================================================================

class CountryConfig(BaseModel):
    """国家配置（与 CountryProfile 兼容）"""
    country_code: str = Field(description="国家代码")
    country_name: str = Field(description="国家名称")
    country_name_zh: str = Field(description="国家中文名称", default="")
    language_code: str = Field(description="语言代码")
    grades: List[Dict[str, str]] = Field(description="年级列表（对象数组，包含 local_name 和 zh_name）")
    subjects: List[Dict[str, str]] = Field(description="学科列表（对象数组，包含 local_name 和 zh_name）")
    grade_subject_mappings: Dict[str, Dict[str, Any]] = Field(description="年级-学科配对信息", default_factory=dict)
    domains: List[str] = Field(description="域名白名单", default_factory=list)
    notes: str = Field(description="说明", default="")


# ============================================================================
# 配置管理器
# ============================================================================

class ConfigManager:
    """国家配置管理器"""
    
    def __init__(self, config_file: str = "data/config/countries_config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self._ensure_config_file()
    
    def _ensure_config_file(self):
        """确保配置文件存在，如果不存在则创建空配置"""
        if not os.path.exists(self.config_file):
            self._write_config({})
    
    def _read_config(self) -> Dict:
        """读取配置文件（使用安全路径操作）"""
        try:
            if not os.path.exists(self.config_file):
                return {}

            # ✅ 安全修复：使用安全的JSON读取（Issue #040: Path Traversal - FIXED）
            # 分离目录和文件名
            config_dir = os.path.dirname(self.config_file) or '.'
            config_filename = os.path.basename(self.config_file)

            # 使用配置文件的目录作为base_dir
            return safe_read_json(config_dir, config_filename)

        except Exception as e:
            print(f"[⚠️ 警告] 读取配置文件失败: {str(e)}")
            return {}

    def _write_config(self, config: Dict):
        """写入配置文件（使用安全路径操作）"""
        try:
            # ✅ 安全修复：使用安全的JSON写入（原子操作，防止路径遍历）
            # 分离目录和文件名
            config_dir = os.path.dirname(self.config_file) or '.'
            config_filename = os.path.basename(self.config_file)

            safe_write_json(config_dir, config_filename, config)

        except Exception as e:
            raise ValueError(f"写入配置文件失败: {str(e)}")
    
    def get_country_config(self, country_code: str) -> Optional[CountryConfig]:
        """
        获取指定国家的配置
        
        Args:
            country_code: 国家代码（如：ID, PH, JP）
        
        Returns:
            CountryConfig 对象，如果不存在则返回 None
        """
        config = self._read_config()
        country_code_upper = country_code.upper()
        
        if country_code_upper not in config:
            return None
        
        try:
            data = config[country_code_upper]
            return CountryConfig(**data)
        except Exception as e:
            print(f"[⚠️ 警告] 解析国家配置失败 ({country_code}): {str(e)}")
            return None
    
    def update_country_config(self, profile: CountryProfile):
        """
        更新或创建国家配置

        Args:
            profile: CountryProfile 对象
        """
        config = self._read_config()
        country_code_upper = profile.country_code.upper()

        # 转换为字典格式
        config[country_code_upper] = {
            "country_code": profile.country_code,
            "country_name": profile.country_name,
            "country_name_zh": profile.country_name_zh,
            "language_code": profile.language_code,
            "grades": profile.grades,
            "subjects": profile.subjects,
            "grade_subject_mappings": profile.grade_subject_mappings,
            "domains": profile.domains,
            "notes": profile.notes
        }

        self._write_config(config)
        print(f"[✅ 成功] 已更新国家配置: {country_code_upper} ({profile.country_name})")
    
    def get_all_countries(self) -> List[Dict]:
        """
        获取所有已配置的国家列表
        
        Returns:
            国家列表，每个元素包含 country_code 和 country_name
        """
        config = self._read_config()
        countries = []
        
        for code, data in config.items():
            countries.append({
                "country_code": code,
                "country_name": data.get("country_name", code)
            })
        
        # 按国家代码排序
        countries.sort(key=lambda x: x["country_code"])
        return countries
    
    def delete_country_config(self, country_code: str) -> bool:
        """
        删除国家配置
        
        Args:
            country_code: 国家代码
        
        Returns:
            是否成功删除
        """
        config = self._read_config()
        country_code_upper = country_code.upper()
        
        if country_code_upper not in config:
            return False
        
        del config[country_code_upper]
        self._write_config(config)
        print(f"[✅ 成功] 已删除国家配置: {country_code_upper}")
        return True


# ============================================================================
# 辅助函数
# ============================================================================

def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    return ConfigManager()


if __name__ == "__main__":
    # 测试代码
    manager = ConfigManager()
    
    # 测试：创建示例配置
    from tools.discovery_agent import CountryProfile
    
    test_profile = CountryProfile(
        country_code="ID",
        country_name="Indonesia",
        language_code="id",
        grades=["Kelas 1", "Kelas 2", "Kelas 3", "Kelas 4", "Kelas 5", "Kelas 6", 
                "Kelas 7", "Kelas 8", "Kelas 9", "Kelas 10", "Kelas 11", "Kelas 12"],
        subjects=["Matematika", "IPA", "IPS", "Bahasa Indonesia", "Bahasa Inggris", 
                  "Pendidikan Agama", "PKN", "Seni Budaya"],
        domains=["ruangguru.com", "zenius.net"],
        notes="印尼 K12 教育体系"
    )
    
    manager.update_country_config(test_profile)
    
    # 测试：读取配置
    config = manager.get_country_config("ID")
    if config:
        print(f"\n✅ 读取配置成功:")
        print(f"   国家: {config.country_name}")
        print(f"   年级数量: {len(config.grades)}")
        print(f"   学科数量: {len(config.subjects)}")
    
    # 测试：获取所有国家
    countries = manager.get_all_countries()
    print(f"\n✅ 已配置的国家数量: {len(countries)}")
    for country in countries:
        print(f"   - {country['country_code']}: {country['country_name']}")

