"""Synthetic HR data generator, structured like SAP HCM infotypes.

All data is fictitious. The table structure is *inspired by* SAP HCM
(PA0000, PA0001, PA0002, PA0007, PA2001); codes are defined by this project.
"""

from hr_generator.config import GeneratorConfig
from hr_generator.dataset import Dataset, generate

__all__ = ["Dataset", "GeneratorConfig", "generate"]
