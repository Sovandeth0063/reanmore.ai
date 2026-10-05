"""
File: orchestrator/app/services/llm/controller.py
Description: Public interface for LLMController and llm_controller singleton.
"""

from app.services.llm.manager import LLMController, llm_service

# llm_controller is the global singleton LLMController instance
llm_controller = llm_service

__all__ = ["LLMController", "llm_controller"]
