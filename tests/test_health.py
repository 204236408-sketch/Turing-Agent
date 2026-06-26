from __future__ import annotations
import sys
from pathlib import Path

# 自动适配项目路径，Windows PowerShell无需手动配置PYTHONPATH
BASE_DIR = Path(__file__).parent.parent
BACKEND_PATH = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_PATH))

from backend.config import settings
from backend.services.chroma_service import chroma_status


def test_config_app_env_values():
    """校验配置文件应用名称、环境参数"""
    assert settings.app_name == "Turing 408 Agent"
    assert settings.app_env in ("dev", "prod", "test")


def test_config_database_url_type():
    """校验数据库地址解析逻辑"""
    db_url = settings.active_database_url
    assert db_url.startswith("sqlite://") or db_url.startswith("mysql")


def test_config_llm_switch_logic():
    """校验LLM启用开关逻辑"""
    raw_key = settings.siliconflow_api_key.strip()
    expect_enabled = bool(raw_key)
    assert settings.llm_enabled == expect_enabled
    assert isinstance(settings.siliconflow_base_url, str)
    assert isinstance(settings.siliconflow_model, str)


def test_chroma_service_status_structure():
    """本地直接调用chroma_status，校验向量库返回结构，不碰接口"""
    chroma_info = chroma_status()
    required_fields = ["enabled", "mode", "path", "error", "collections"]
    for field in required_fields:
        assert field in chroma_info
    assert isinstance(chroma_info["collections"], list)
    
    # 统一标准化路径，消除正反斜杠、相对路径差异
    actual_path = Path(chroma_info["path"]).resolve()
    config_path = Path(settings.chroma_path).resolve()
    assert actual_path == config_path


def test_config_path_settings():
    """校验向量库、上传、报告目录配置存在"""
    assert isinstance(settings.chroma_path, str)
    assert isinstance(settings.upload_dir, str)
    assert isinstance(settings.report_dir, str)


if __name__ == "__main__":
    import pytest
    pytest.main(["-v", "-s", __file__])