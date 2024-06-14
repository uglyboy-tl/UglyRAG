from dataclasses import dataclass

from .base import Refiner


@dataclass
class ExtractiveRefiner(Refiner):
    """Implementation for Extractive compressor.
    Using retrieval method to select sentences or other granularity data.
    """

    _name_ = "Extractive"

    pass
