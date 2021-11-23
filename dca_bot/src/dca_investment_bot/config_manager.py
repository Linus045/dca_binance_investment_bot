import json
import os
import typing
from typing import Any

from dca_investment_bot.logger import LOG_CRITICAL
from dca_investment_bot.logger import LOG_ERROR
from dca_investment_bot.logger import LOG_WARNING
from dca_investment_bot.paths import Paths

"""
Manages all the options stored in config.json.
Loads and validates the options.

current Options.json:
{
    "LOGGING" : {
        "LOG_LEVEL" : "DEBUG",
        "LOG_FILE" : "bot.log"
    },
    "USE_TESTNET" : true,
    "CHECK_INTERVAL" : 1800,
    "SYNC_FULFILLED_ORDERS_TO_FIREBASE" : false,
    "USE_FIREBASE" : false,
    "FIREBASE_PROJECT_ID" : ""
}
"""


class ConfigManager:
    KEY_LOGGING = "LOGGING"
    KEY_LOG_LEVEL = "LOG_LEVEL"
    KEY_LOG_FILE = "LOG_FILE"
    KEY_USE_TESTNET = "USE_TESTNET"
    KEY_CHECK_INTERVAL = "CHECK_INTERVAL"
    KEY_SYNC_FULFILLED_ORDERS_TO_FIREBASE = "SYNC_FULFILLED_ORDERS_TO_FIREBASE"
    KEY_USE_FIREBASE = "USE_FIREBASE"
    KEY_FIREBASE_PROJECT_ID = "FIREBASE_PROJECT_ID"

    def __init__(self) -> None:
        self.debug_tag = "[ConfigManager]"
        self.log_level: Any = None
        self.log_file: Any = None
        self.use_testnet: Any = None
        self.check_interval: Any = None
        self.sync_fulfilled_orders_to_firebase: Any = None
        self.use_firebase: Any = None
        self.firebase_project_id: Any = None

    def __validate_value(
        self,
        data: typing.Dict,
        key: str,
        expected_type: type,
        default_value: Any,
        valid_values: typing.List = None,
        valid_filepath: bool = False,
    ) -> Any:
        """
        Validates a value in the config file.
        If the value is not found or is not of the
        correct type, the default value is returned.
        """
        value = self.get_value_or_default(data, key, default_value)
        try:
            if expected_type is bool:
                if value is not True and value is not False:
                    raise ValueError("Value is not boolean")
            elif expected_type is int:
                if not isinstance(value, int):
                    raise ValueError("Value is not integer")
            elif expected_type is str:
                if not isinstance(value, str):
                    raise ValueError("Value is not string")
                if valid_filepath and not os.path.exists(value):
                    raise ValueError("Value is not a valid filepath")
                if valid_values is not None and value not in valid_values:
                    raise ValueError("Value is not in list of valid values")
            elif expected_type is list:
                if not isinstance(value, list):
                    raise ValueError("Value is not a list")
            else:
                raise ValueError(f"Value is not of type {expected_type}")
        except ValueError:
            LOG_ERROR(
                self.debug_tag,
                f"Value for key {key} is invalid. Using default value: {default_value}",
            )
            value = default_value
        return value

    def get_value_or_default(self, data: typing.Dict, key: str, default_value: Any) -> Any:
        """
        Returns the value for the given key in the config file.
        If the key is not found, the default value is returned.
        """
        if key in data:
            return data[key]
        else:
            LOG_CRITICAL(
                self.debug_tag,
                f"Key {key} not found in config file. Using default value: {default_value}",
            )
            return default_value

    def load_and_validate_config(self) -> None:
        """
        Loads and validates the config file.
        """
        with open(Paths.config_filepath) as json_file:
            data = json.load(json_file)

            # Logging section
            if self.KEY_LOGGING not in data:
                LOG_WARNING(
                    self.debug_tag,
                    "No logging section found in config.json. Using default values.",
                )
                data[self.KEY_LOGGING] = {
                    self.KEY_LOG_LEVEL: "DEBUG",
                    self.KEY_LOG_FILE: "bot.log",
                }

            logging_data = data[self.KEY_LOGGING]
            self.log_level = self.__validate_value(
                logging_data,
                self.KEY_LOG_LEVEL,
                str,
                "DEBUG",
                ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            )
            self.log_file = self.__validate_value(logging_data, self.KEY_LOG_FILE, str, Paths.default_log_filename)
            self.use_testnet = self.__validate_value(data, self.KEY_USE_TESTNET, bool, True)
            self.check_interval = self.__validate_value(data, self.KEY_CHECK_INTERVAL, int, 1800)
            self.sync_fulfilled_orders_to_firebase = self.__validate_value(
                data, self.KEY_SYNC_FULFILLED_ORDERS_TO_FIREBASE, bool, False
            )
            self.use_firebase = self.__validate_value(data, self.KEY_USE_FIREBASE, bool, False)
            self.firebase_project_id = self.__validate_value(data, self.KEY_FIREBASE_PROJECT_ID, str, "")
