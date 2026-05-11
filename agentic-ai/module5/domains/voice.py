# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from module5.engine.domain_adapter import DomainConfig, PromptLayers, GuardrailPolicy

VOICE_DOMAIN = DomainConfig(
    name="voice_interaction",
    display_name="Voice Interaction Specialist",
    prompt_layers=PromptLayers(
        role="You are a Voice Interaction Specialist that processes speech input and "
             "produces speech-optimized output for the DevOps Companion platform.",
        knowledge_context="You handle speech-to-text transcription via Deepgram and Amazon Transcribe, "
                          "and text-to-speech synthesis via Deepgram Aura and Amazon Polly. "
                          "Format all responses for natural spoken delivery.",
        constraints="Responses MUST be under 3 sentences. Never output markdown, code blocks, "
                    "bullet points, or formatted text. Never output URLs or file paths. "
                    "Never speak passwords, secret keys, or access keys aloud. "
                    "Use confirmation patterns: 'I've done X, shall I continue?'",
        communication="Conversational, concise. Use natural spoken language patterns. "
                      "Prefer short declarative sentences. Avoid technical jargon unless necessary. "
                      "Always confirm actions before executing them.",
    ),
    tool_names=[
        "deepgram_transcribe",
        "deepgram_synthesize",
        "transcribe_audio",
        "polly_synthesize",
    ],
    guardrail_policy=GuardrailPolicy(
        pii_handling="ANONYMIZE",
        pii_entities=["NAME", "PHONE", "EMAIL", "US_SSN"],
        denied_topics=[],
        content_filters={"MISCONDUCT": "HIGH"},
        word_filters=["password", "secret key", "access key"],
    ),
    evaluation_criteria={
        "response_brevity": "Response is 3 sentences or fewer",
        "speech_naturalness": "No markdown, code, URLs, or formatted text in output",
        "transcription_handling": "Handles low-confidence transcriptions with clarification",
        "latency_awareness": "Response length appropriate for voice latency budget",
    },
)
