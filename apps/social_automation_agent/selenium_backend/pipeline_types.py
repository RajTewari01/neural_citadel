'''
pipelines_types.py - A  base class to create a unified look among all automation scripts
'''

from typing import Optional , Dict,  List, Union, Literal
from dataclasses import dataclass


@dataclass
class PipelineConfig:

    def __post_init__(self):pass
    