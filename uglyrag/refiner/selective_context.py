# Implementation of Selective-Context, modified from official repo: https://github.com/liyucheng09/Selective_Context
# Licensed under The MIT License

from dataclasses import dataclass

from .base import Refiner


@dataclass
class SelectiveContextRefiner(Refiner):
    """Implementation for Extractive compressor.
    Using retrieval method to select sentences or other granularity data.
    """

    _name_ = "SelectiveContext"

    pass
