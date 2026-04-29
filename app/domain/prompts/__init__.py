"""Domain prompts for P2P bot."""
from .semantic_markers import (
    IMAGE_ANALYSIS_TAG,
    VOICE_TRANSCRIPTION_TAG,
    PAYMENT_PROOF_TAG,
    SYSTEM_CONTEXT_TAG,
    format_image_message,
    format_voice_message,
    format_payment_proof,
    format_context_message
)

__all__ = [
    "IMAGE_ANALYSIS_TAG",
    "VOICE_TRANSCRIPTION_TAG",
    "PAYMENT_PROOF_TAG",
    "SYSTEM_CONTEXT_TAG",
    "format_image_message",
    "format_voice_message",
    "format_payment_proof",
    "format_context_message"
]
