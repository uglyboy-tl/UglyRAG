from __future__ import annotations

import configparser
import logging
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, StreamHandler
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from uglyrag._config import Config, configure_logger, singleton

logging.basicConfig(level=logging.CRITICAL)


# 测试用的简单类，用于验证singleton装饰器
@singleton
class TestSingletonClass:
    def __init__(self, value):
        self.value = value


@pytest.fixture
def config_instance():
    config = Config()
    config.config = configparser.ConfigParser()
    return config


# 创建一个Config对象的fixture
@pytest.fixture
def config_save_fixture(tmp_path):
    config = Config()
    config.config = MagicMock(spec=configparser.ConfigParser)
    config.config_path = tmp_path / "test_config.ini"
    config._changed = False  # 假设配置已更改，需要保存
    return config


def test_singleton_creation():
    # 测试实例的创建
    instance1 = TestSingletonClass(10)
    instance2 = TestSingletonClass(10)

    # 验证是否为同一个实例
    assert instance1 is instance2
    assert instance1.value == instance2.value


def test_singleton_different_args():
    # 使用不同的参数实例化类，验证是否仍然为同一个实例
    instance1 = TestSingletonClass(10)
    instance2 = TestSingletonClass(20)

    assert instance1 is instance2
    assert instance1.value == instance2.value


def test_configure_logger_level():
    logger = StreamHandler()
    configure_logger(logger, "DEBUG")
    assert logger.level == DEBUG

    configure_logger(logger, "INFO")
    assert logger.level == INFO

    configure_logger(logger, "WARNING")
    assert logger.level == WARNING

    configure_logger(logger, "ERROR")
    assert logger.level == ERROR

    configure_logger(logger, "CRITICAL")
    assert logger.level == CRITICAL

    configure_logger(logger, "INVALID_LEVEL")
    assert logger.level == INFO


def test_get_option_exists(config_instance):
    config_instance.config.read_string("""
    [TEST]
    test_option = test_value
    """)
    result = config_instance.get("test_option", "TEST")
    assert result == "test_value"


def test_get_option_exists_with_default(config_instance):
    config_instance.config.read_string("""
    [TEST]
    test_option = test_value
    """)
    result = config_instance.get("test_option", "TEST", default="default_value")
    assert result == "test_value"


def test_get_option_not_exists_without_default(config_instance):
    config_instance.config.read_string("""
    [TEST]
    other_option = other_value
    """)
    result = config_instance.get("non_existent_option", "TEST")
    assert result == ""


def test_get_option_not_exists_with_default(config_instance):
    config_instance.config.read_string("""
    [TEST]
    other_option = other_value
    """)
    result = config_instance.get("non_existent_option", "TEST", default="default_value")
    assert result == "default_value"


def test_get_option_in_non_default_section(config_instance):
    config_instance.config.read_string("""
    [ANOTHER_TEST]
    another_option = another_value
    """)
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
def test_save_config_file_unchanged(config_save_fixture):
    config_save_fixture.config["DEFAULT"] = {"Setting1": "Value1"}
    with patch.object(Path, "open", mock_open()) as mocked_file:
        config_save_fixture.save()

        # 检查文件是否没有被打开
        mocked_file.assert_not_called()

        # 检查配置内容是否没有被写入
        config_save_fixture.config.write.assert_not_called()

        # 检查更改标志是否仍然为未更改状态
        assert config_save_fixture._changed is False


# 测试：如果配置没有变化，则不写入文件
def test_save_config_file_changed(config_save_fixture):
    config_save_fixture.config["DEFAULT"] = {"Setting1": "Value1"}
    config_save_fixture._changed = True  # 手动设置配置已更改
    with patch.object(Path, "open", mock_open()) as mocked_file:
        config_save_fixture.save()

        # 检查文件是否以写模式打开
        mocked_file.assert_called_once_with("w")  # 检查是否调用了写入方法

        # 检查是否正确写入配置内容
        handle = mocked_file()
        config_save_fixture.config.write.assert_called_once_with(handle)

        # 检查更改标志是否已重置
        assert config_save_fixture._changed is False


# 测试：如果配置没有变化，则不写入文件
def test_config_file_set_changed(config_save_fixture):
    config_save_fixture.set("Setting1", "Value1")
    with patch.object(Path, "open", mock_open()) as mocked_file:
        config_save_fixture.save()

        # 检查文件是否以写模式打开
        mocked_file.assert_called_once_with("w")  # 检查是否调用了写入方法

        # 检查是否正确写入配置内容
        handle = mocked_file()
        config_save_fixture.config.write.assert_called_once_with(handle)

        # 检查更改标志是否已重置
        assert config_save_fixture._changed is False
