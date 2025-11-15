"""
Test suite for generate_review method.
Tests review generation, diff truncation, and timing.
"""

import pytest
import numpy as np
import unittest
from unittest.mock import Mock, patch, MagicMock
import time # Import time for the original method, though we mock it in tests

from online_estimator_version import IterativePromptSelector


class TestGenerateReview:
    """Tests for generate_review method."""
    
    def test_successful_review_generation(self, selector_instance, mock_dependencies):
        """Test successful review generation."""
        diff_text = "def foo():\n    pass"
        
        mock_chain = Mock()
        mock_chain.invoke = Mock(return_value="Great code review!")
        selector_instance.prompts['detailed'].__or__ = Mock(return_value=mock_chain)
        
        with patch('iterative_prompt_selector.run_static_analysis', mock_dependencies['run_static_analysis']), \
             patch('iterative_prompt_selector.safe_truncate', mock_dependencies['safe_truncate']):
            
            review, elapsed, static, context = selector_instance.generate_review(diff_text, 'detailed')
            
            assert review == "Great code review!"
            assert isinstance(elapsed, float)
            assert static == "No issues found"
            assert "Best practice" in context
    
    def test_static_analysis_failure_handling(self, selector_instance, mock_dependencies):
        """Test handling of static analysis failure."""
        diff_text = "def foo():\n    pass"
        
        mock_chain = Mock()
        mock_chain.invoke = Mock(return_value="Review text")
        selector_instance.prompts['detailed'].__or__ = Mock(return_value=mock_chain)
        
        with patch('iterative_prompt_selector.run_static_analysis', side_effect=ValueError("Static analysis error")), \
             patch('iterative_prompt_selector.safe_truncate', mock_dependencies['safe_truncate']):
            
            review, elapsed, static, context = selector_instance.generate_review(diff_text, 'detailed')
            
            assert "Static analysis failed" in static
    
    def test_rag_retrieval_failure_handling(self, selector_instance, mock_dependencies):
        """Test handling of RAG retrieval failure."""
        diff_text = "def foo():\n    pass"
        
        mock_chain = Mock()
        mock_chain.invoke = Mock(return_value="Review text")
        selector_instance.prompts['concise'].__or__ = Mock(return_value=mock_chain)
        selector_instance.retriever.invoke = Mock(side_effect=RuntimeError("RAG error"))
        
        with patch('iterative_prompt_selector.run_static_analysis', mock_dependencies['run_static_analysis']), \
             patch('iterative_prompt_selector.safe_truncate', mock_dependencies['safe_truncate']):
            
            review, elapsed, static, context = selector_instance.generate_review(diff_text, 'concise')
            
            assert "RAG retrieval failed" in context
    
    def test_llm_invocation_failure_handling(self, selector_instance, mock_dependencies):
        """Test handling of LLM invocation failure."""
        diff_text = "def foo():\n    pass"
        
        mock_chain = Mock()
        mock_chain.invoke = Mock(side_effect=RuntimeError("LLM error"))
        selector_instance.prompts['security'].__or__ = Mock(return_value=mock_chain)
        
        with patch('iterative_prompt_selector.run_static_analysis', mock_dependencies['run_static_analysis']), \
             patch('iterative_prompt_selector.safe_truncate', mock_dependencies['safe_truncate']):
            
            review, elapsed, static, context = selector_instance.generate_review(diff_text, 'security')
            
            assert "LLM invocation failed" in review
    
    def test_truncation_applied(self, selector_instance, mock_dependencies):
        """Test that truncation is applied to inputs."""
        diff_text = "x" * 10000
        
        mock_chain = Mock()
        mock_chain.invoke = Mock(return_value="Review")
        selector_instance.prompts['detailed'].__or__ = Mock(return_value=mock_chain)
        
        with patch('iterative_prompt_selector.run_static_analysis', mock_dependencies['run_static_analysis']), \
             patch('iterative_prompt_selector.safe_truncate', mock_dependencies['safe_truncate']) as mock_truncate:
            
            selector_instance.generate_review(diff_text, 'detailed')
            
            assert mock_truncate.call_count >= 3
