"""Message processing handlers."""
from .message_processor import message_processor, ProcessingResult
from .spam_detector import spam_detector, SpamAnalysisResult

__all__ = [
    "message_processor", 
    "ProcessingResult",
    "spam_detector",
    "SpamAnalysisResult"
]
