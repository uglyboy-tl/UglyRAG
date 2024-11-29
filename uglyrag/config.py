import configparser
import logging
import threading
from datetime import datetime
from functools import wraps
from pathlib import Path

import appdirs


# 单例修饰器
def singleton(cls):
    instances = {}  # 存储类的实例
    lock = threading.Lock()  # 锁对象，保证线程安全

    @wraps(cls)  # 保持原类的元数据
    def get_instance(*args, **kwargs):
        with lock:  # 保证线程同步
            if cls not in instances:
                logging.info(f"正在创建新的 {cls.__name__} 实例")
                instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


def configure_logger(logger, level_str):
    # 将字符串转换为日志级别常量
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    # 获取传入字符串对应的日志级别，如果没有匹配到则使用默认值
    log_level = levels.get(level_str.upper(), logging.INFO)

    # 设置日志级别
    logger.setLevel(log_level)


@singleton
class Config:
    def __init__(self, app_name="uglyrag"):
        # 基本日志配置
        self._configure_basic_logging()

        # 初始化配置文件
        self.config = configparser.ConfigParser()

        # 读取 INI 文件
        # 获取 XDG 配置目录
        config_dir = Path(appdirs.user_config_dir(app_name, roaming=True))
        data_dir = Path(appdirs.user_data_dir(app_name, roaming=True))
        self.config_path = config_dir / "config.ini"

        try:
            # 读取配置文件
            self.config.read(self.config_path)
            logging.info(f"配置文件读取成功: {self.config_path}")
        except FileNotFoundError:
            logging.warning(f"配置文件未找到: {self.config_path}")
        except configparser.Error as e:
            logging.error(f"解析配置文件时出错: {e}")
        except Exception as e:
            logging.error(f"读取配置文件时发生意外错误: {e}")

        # 初始化配置文件是否发生变化的标志
        self._changed = False

        self.data_dir = self.get("data_dir", section="core", default=str(data_dir))
        # 创建数据目录
        data_dir.mkdir(parents=True, exist_ok=True)

        # 配置日志输出到 data_dir 目录下的 log 文件
        self.configure_logging()

    def _configure_basic_logging(self):
        # 创建日志记录器
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)  # 设置日志记录器的最低级别为 DEBUG

        # 移除已有的处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # 创建流处理器，记录 INFO 及以上级别的日志
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_formatter = logging.Formatter("%(asctime)s - [%(levelname)s] - %(message)s")
        stream_handler.setFormatter(stream_formatter)

        # 添加处理器到日志记录器
        logger.addHandler(stream_handler)

        logging.debug("基本日志配置完成")

    def configure_logging(self):
        # 创建 logs 文件夹
        logs_dir = Path(self.data_dir) / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        log_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        log_level = self.get("level", "logging", "info")

        # 创建日志记录器
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)  # 设置日志记录器的最低级别为 DEBUG

        # 移除已有的处理器
        if logger.handlers:
            logger.removeHandler(logger.handlers[0])

        # 创建文件处理器，记录所有级别的日志
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter("%(asctime)s - [%(levelname)s] - %(message)s")
        file_handler.setFormatter(file_formatter)

        # 创建流处理器，记录 INFO 及以上级别的日志
        stream_handler = logging.StreamHandler()
        configure_logger(stream_handler, log_level)
        stream_formatter = logging.Formatter("%(asctime)s - [%(levelname)s] - %(message)s")
        stream_handler.setFormatter(stream_formatter)

        # 添加处理器到日志记录器
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

        logging.debug(f"日志文件已配置为: {log_file}")

    def get(self, option, section="core", default=None):
        try:
            value = self.config.get(section, option)
            logging.debug(f"从节 '{section}' 中获取选项 '{option}': {value}")
            return value
        except (configparser.NoSectionError, configparser.NoOptionError):
            if default is None:
                return None
            logging.warning(f"节 '{section}' 中未找到选项 '{option}'，使用默认值: {default}")
            self.set(option, default, section)
            return default

    def set(self, option, value, section="core"):
        if not option:
            raise ValueError("节和选项不能为空或 None")

        # 基本验证以防止注入攻击
        if not (isinstance(value, str) or isinstance(value, int) or isinstance(value, float)):
            raise TypeError("值必须是字符串或数字")

        try:
            self.config.set(section, option, str(value))
            logging.info(f"在节 '{section}' 中设置选项 '{option}' 为: {value}")
        except configparser.NoSectionError:
            logging.info(f"添加节 '{section}'")
            self.config.add_section(section)
            self.config.set(section, option, str(value))
            logging.info(f"在节 '{section}' 中设置选项 '{option}' 为: {value}")

        self._changed = True  # 标记配置文件已更改

    # 保存配置文件
    def save(self):
        # 如果配置文件没有变化，则不需要重新写入
        if not self._changed:
            logging.debug("配置文件没有变化，无需保存。")
            return

        # 确保配置文件存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w") as configfile:
            self.config.write(configfile)
            logging.info(f"配置文件保存成功: {self.config_path}")

        # 重置更改标志
        self._changed = False

    # 注销 Config 实例时，保存配置文件
    def __del__(self):
        self.save()
        logging.debug(f"{self.__class__.__name__} 实例正在被删除，配置已保存。")
