"""Helpful dataclasses to make the rest of the program more type safe"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class GridNodeData:
    """Represents data of a single grid node"""
    name: Optional[str]
    host: str
    port: int
