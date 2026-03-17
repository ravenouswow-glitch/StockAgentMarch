from abc import ABC, abstractmethod
from typing import List, Dict, Any

class IOutputHandler(ABC):
    @abstractmethod
    def initialize(self) -> bool:
        pass
    
    @abstractmethod
    def write(self, ticker: str, data: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    def write_batch(self, data: List[Dict[str, Any]]) -> bool:
        pass
    
    @abstractmethod
    def close(self):
        pass