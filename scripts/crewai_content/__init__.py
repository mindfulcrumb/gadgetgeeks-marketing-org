"""
CrewAI Content Pipeline for Gadget Geeks Pro.

Sequential multi-agent pipeline: Research -> Write -> SEO -> QA.
Uses Claude as LLM backend via langchain-anthropic.

Usage:
    from scripts.crewai_content.crew import run_content_pipeline
    result = run_content_pipeline(topic="refurbished iPhone 15 buying guide")
"""

from .crew import run_content_pipeline

__all__ = ["run_content_pipeline"]
