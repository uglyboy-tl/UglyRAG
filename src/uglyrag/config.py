from __future__ import annotations

import configparser
import logging
from datetime import datetime
from pathlib import Path

import appdirs

from .logger import configure_basic_logging, configure_file_logging
from .singleton import singleton


@singleton
class Config:
    def __init__(self, app_name: str = "uglyrag") -> None:
        # 基本日志配置
        configure_basic_logging()

        # 初始化配置文件
        self.config = configparser.ConfigParser()

        # 读取 INI 文件
        # 获取 XDG 配置目录
        config_dir = Path(appdirs.user_config_dir(app_name, roaming=True))
        self.config_path = config_dir / "config.ini"

        try:
            # 读取配置文件
            self.config.read(self.config_path)
            logging.debug(f"配置文件读取成功: {self.config_path}")
        except FileNotFoundError:
            logging.warning(f"配置文件未找到: {self.config_path}")
        except configparser.Error as e:
            logging.error(f"解析配置文件时出错: {e}")
        except Exception as e:
            logging.error(f"读取配置文件时发生意外错误: {e}")

        data_dir = appdirs.user_data_dir(app_name, roaming=True)
        self.data_dir: Path = Path(self.get("data_dir", section="DEFAULT", default=data_dir))
        # 创建数据目录
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 配置日志输出到 data_dir 目录下的 log 文件
        self.configure_logging()

        # 初始化配置文件是否发生变化的标志
        self._changed = False

    def configure_logging(self) -> None:
        log_level = self.get("level", "LOGGING", "info")
        configure_file_logging(self.data_dir, log_level)

    def get(self, option: str, section: str = "DEFAULT", default: str = "") -> str:
        try:
            value = self.config.get(section, option)
            logging.debug(f"从节 '{section}' 中获取选项 '{option}': {value}")
            return value
        except (configparser.NoSectionError, configparser.NoOptionError):
            if default:
                logging.debug(f"节 '{section}' 中未找到选项 '{option}'，使用默认值: {default}")
                self.set(option, default, section)
            else:
                logging.debug(f"节 '{section}' 中未找到选项 '{option}', 返回 \"\"")
            return default

    def set(self, option: str, value: str, section: str = "DEFAULT") -> None:
        if not option or not section:
            raise ValueError("节和选项不能为空或 None")

        # 基本验证以防止注入攻击
        if not (isinstance(value, str) or isinstance(value, int) or isinstance(value, float)):
            raise TypeError("值必须是字符串或数字")

        try:
            self.config.set(section, option, str(value))
            logging.debug(f"在节 '{section}' 中设置选项 '{option}' 为: {value}")
        except configparser.NoSectionError:
            logging.debug(f"添加节 '{section}'")
            self.config.add_section(section)
            self.config.set(section, option, str(value))
            logging.debug(f"在节 '{section}' 中设置选项 '{option}' 为: {value}")

        self._changed = True  # 标记配置文件已更改

    # 保存配置文件
    def save(self) -> None:
        # 如果配置文件没有变化，则不需要重新写入
        if not self._changed:
            logging.debug("配置文件没有变化，无需保存。")
            return

        # 确保配置文件存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w") as configfile:
            self.config.write(configfile)
            logging.debug(f"配置文件保存成功: {self.config_path}")

        # 重置更改标志
        self._changed = False

    # 注销 Config 实例时，保存配置文件
    def __del__(self) -> None:
        self.save()
        logging.debug(f"{self.__class__.__name__} 实例正在被删除，配置已保存。")


config = Config()
