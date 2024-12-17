from __future__ import annotations

import logging
from collections.abc import Callable


def load_module(
    function: Callable[[], Callable | None], attribute_name: str, target: object, warning_message: str
) -> None:
    try:
        attribute = function()
        if attribute is not None:
            setattr(target, attribute_name, attribute)
    except Exception as e:
        logging.debug(e)
        logging.warning(warning_message)
