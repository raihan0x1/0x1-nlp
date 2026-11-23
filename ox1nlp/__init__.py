"""
0x1NLP - Advanced Indonesian Natural Language Processing Library
"""

# Import main modules
from . import datasets, preprocessing
from .datasets import DatasetLoader
from .preprocessing import Pipeline

# Version info
__version__ = "1.7.0"
__author__ = "Raihan Hidayatullah Djunaedi"
__email__ = "raihanhd.dev@gmail.com"

# Export main modules
__all__ = ["DatasetLoader", "Pipeline", "datasets", "preprocessing"]
