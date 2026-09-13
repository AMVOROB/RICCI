# Органы ощущений (УР.1): чувствуют ΔS, а не «картину мира».
from .base import Sensor, Delta
from .text import TextSensor
from .body import BodySensor
from .graph import GraphSensor

__all__ = ["Sensor", "Delta", "TextSensor", "BodySensor", "GraphSensor"]