"""
Image Surgeon - AI Image Manipulation
======================================
Professional pipeline for background replacement and clothes change.
Uses SAM2, SegFormer, CatVTON.
"""

from .engine import ImageSurgeonEngine
from .pipeline.pipeline_types import SurgeonConfig

__all__ = ['ImageSurgeonEngine', 'SurgeonConfig']
