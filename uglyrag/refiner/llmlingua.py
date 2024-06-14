# Implementation of LLMLingua, modified from official repo: https://github.com/microsoft/LLMLingua.
# Copyright (c) 2023 Microsoft
# Licensed under The MIT License

from dataclasses import dataclass

from .base import Refiner


@dataclass
class LLMLinguaRefiner(Refiner):
    """Implementation for Extractive compressor.
    Using retrieval method to select sentences or other granularity data.
    """

    _name_ = "LLMLingua"

    pass
