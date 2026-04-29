"""
Semantic markers for P2P bot messages.

These markers structure multimodal content and provide context for AI agents.
"""

IMAGE_ANALYSIS_TAG = "[IMAGE_ANALYSIS]"
VOICE_TRANSCRIPTION_TAG = "[VOICE]"
PAYMENT_PROOF_TAG = "[PAYMENT_PROOF]"
SYSTEM_CONTEXT_TAG = "[CONTEXT]"

def format_image_message(caption: str, analysis: str) -> str:
    """Format image message with semantic marker."""
    parts = []
    if caption:
        parts.append(caption)
    parts.append(f"{IMAGE_ANALYSIS_TAG} {analysis}")
    return " ".join(parts)

def format_voice_message(transcription: str) -> str:
    """Format voice transcription with semantic marker."""
    return f"{VOICE_TRANSCRIPTION_TAG} {transcription}"

def format_payment_proof(image_analysis: str, extracted_data: dict) -> str:
    """Format payment proof with extracted data."""
    data_str = " | ".join(f"{k}: {v}" for k, v in extracted_data.items() if v)
    return f"{PAYMENT_PROOF_TAG} {image_analysis} [{data_str}]"

def format_context_message(context: dict) -> str:
    """Format context data for AI processing."""
    lines = [f"{k}: {v}" for k, v in context.items() if v is not None]
    return f"{SYSTEM_CONTEXT_TAG}\n" + "\n".join(lines)
