"""
Base class for all module data classes
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ModuleData(ABC):
    """Abstract Base class for all module data classes"""

    @abstractmethod
    def to_abi_encoded(self):
        """Return the data in ABI encoded format"""
        raise NotImplementedError

    @abstractmethod
    def to_json(self):
        """Return the data in JSON format"""
        raise NotImplementedError
