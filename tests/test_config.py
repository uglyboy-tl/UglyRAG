from __future__ import annotations

import configparser
import logging
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from uglyrag.config import Config

logging.basicConfig(level=logging.CRITICAL)


@pytest.fixture
def config_instance():
    config = Config()
    config.config = configparser.ConfigParser()
    return config


def setup_config(config_instance, section: str, option: str, value: str):
    """辅助函数：设置配置内容"""
    config_instance.config.read_string(f"""
    [{section}]
    {option} = {value}
    """)


def test_config_initialization():
    config = Config()
    assert config.config_path.name == "config.ini"
    assert config.data_dir.name == "uglyrag"
    assert config._changed is False


def test_get_option_exists(config_instance):
    setup_config(config_instance, "TEST", "test_option", "test_value")
    result = config_instance.get("test_option", "TEST")
    assert result == "test_value"


def test_get_option_exists_with_default(config_instance):
    setup_config(config_instance, "TEST", "test_option", "test_value")
    result = config_instance.get("test_option", "TEST", default="default_value")
    assert result == "test_value"


def test_get_option_not_exists_without_default(config_instance):
    setup_config(config_instance, "TEST", "other_option", "other_value")
    result = config_instance.get("non_existent_option", "TEST")
    assert result == ""


def test_get_option_not_exists_with_default(config_instance):
    setup_config(config_instance, "TEST", "other_option", "other_value")
    result = config_instance.get("non_existent_option", "TEST", default="default_value")
    assert result == "default_value"


def test_get_option_in_non_default_section(config_instance):
    setup_config(config_instance, "ANOTHER_TEST", "another_option", "another_value")
    result = config_instance.get("another_option", "ANOTHER_TEST")
    assert result == "another_value"


def test_get_option_in_non_existent_section_with_default(config_instance):
    result = config_instance.get("another_option", "NON_EXISTENT", default="default_value")
    assert result == "default_value"


def test_set_valid_option_and_value(config_instance):
    """测试使用有效的节、选项和值设置配置"""
    config_instance.set("option1", "value1")
    assert "option1" in config_instance.config["DEFAULT"]


def test_set_valid_option_and_value_in_custom_section(config_instance):
    """测试在自定义节中使用有效的选项和值设置配置"""
    config_instance.set("option1", "value1", section="custom_section")
    assert "option1" in config_instance.config["custom_section"]


def test_set_option_without_value_raises_type_error(config_instance):
    """测试设置配置时提供非字符串/数字值应引发TypeError"""
    with pytest.raises(TypeError):
        config_instance.set("option1", None)


def test_set_option_without_section_raises_value_error(config_instance):
    """测试在没有节的情况下设置配置应引发ValueError"""
    with pytest.raises(ValueError):
        config_instance.set(None, "value1")


def test_set_option_with_invalid_section_raises_value_error(config_instance):
    """测试使用无效节设置配置应引发ValueError"""
    with pytest.raises(ValueError):
        config_instance.set("option1", "value1", section=None)


def test_set_option_and_create_new_section(config_instance):
    """测试设置一个新节中的配置选项"""
    section_name = "new_section"
    option_name = "new_option"
    option_value = "new_value"

    config_instance.set(option_name, option_value, section=section_name)
    assert section_name in config_instance.config.sections()
    assert option_name in config_instance.config[section_name]


def test_set_option_in_existing_section(config_instance):
    """测试在现有节中设置配置选项"""
    section_name = "existing_section"
    option_name = "existing_option"
    option_value = "updated_value"

    # 假设节已经存在
    config_instance.config.add_section(section_name)
    config_instance.config.set(section_name, option_name, "old_value")

    config_instance.set(option_name, option_value, section=section_name)
    assert section_name in config_instance.config.sections()
    assert option_name in config_instance.config[section_name]
    assert config_instance.config[section_name][option_name] == option_value


# 测试：确保配置文件被写入正确的内容
def test_save_config_file_unchanged(config):
    config.config["DEFAULT"] = {"Setting1": "Value1"}
    with patch.object(Path, "open", mock_open()) as mocked_file:
        config.save()

        # 检查文件是否没有被打开
        mocked_file.assert_not_called()

        # 检查配置内容是否没有被写入
        config.config.write.assert_not_called()

        # 检查更改标志是否仍然为未更改状态
        assert config._changed is False


# 测试：如果配置没有变化，则不写入文件
def test_save_config_file_changed(config):
    config.config["DEFAULT"] = {"Setting1": "Value1"}
    config._changed = True  # 手动设置配置已更改
    with patch.object(Path, "open", mock_open()) as mocked_file:
        config.save()

        # 检查文件是否以写模式打开
        mocked_file.assert_called_once_with("w")  # 检查是否调用了写入方法

        # 检查是否正确写入配置内容
        handle = mocked_file()
        config.config.write.assert_called_once_with(handle)

        # 检查更改标志是否已重置
        assert config._changed is False


# 测试：如果配置没有变化，则不写入文件
def test_config_file_set_changed(config):
    config.set("Setting1", "Value1")
    with patch.object(Path, "open", mock_open()) as mocked_file:
        config.save()

        # 检查文件是否以写模式打开
        mocked_file.assert_called_once_with("w")  # 检查是否调用了写入方法

        # 检查是否正确写入配置内容
        handle = mocked_file()
        config.config.write.assert_called_once_with(handle)

        # 检查更改标志是否已重置
        assert config._changed is False


def test_configure_logging():
    config = Config()
    with patch.object(logging, "getLogger", return_value=logging.getLogger()) as mock_get_logger:
        config.configure_logging()
        mock_get_logger.assert_called()
