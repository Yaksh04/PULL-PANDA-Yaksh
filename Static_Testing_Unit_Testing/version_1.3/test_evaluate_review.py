"""
Test suite for evaluate_review method.
Tests review evaluation and scoring logic.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
from online_estimator_version import IterativePromptSelector


class TestEvaluateReview:
    """Tests for evaluate_review method."""
    
    def test_successful_evaluation(self, selector_instance, mock_dependencies):
        """Test successful review evaluation."""
        diff = "def foo(): pass"
        review = "Good code structure. Consider adding docstrings."
        static = "No issues"
        context = "Best practices"
        
        with patch('iterative_prompt_selector.heuristic_metrics', mock_dependencies['heuristic_metrics']), \
             patch('iterative_prompt_selector.meta_evaluate', mock_dependencies['meta_evaluate']):
            
            score, heur, meta = selector_instance.evaluate_review(diff, review, static, context)
            
            assert isinstance(score, (int, float))
            assert 0 <= score <= 10
            assert isinstance(heur, dict)
            assert isinstance(meta, dict)
    
    def test_evaluation_with_meta_error(self, selector_instance, mock_dependencies):
        """Test evaluation when meta-evaluation returns error."""
        with patch('iterative_prompt_selector.heuristic_metrics', mock_dependencies['heuristic_metrics']), \
             patch('iterative_prompt_selector.meta_evaluate', return_value=({'error': 'Failed'}, "")):
            
            score, heur, meta = selector_instance.evaluate_review("diff", "review", "static", "context")
            
            assert score == 5.0
    
    def test_evaluation_score_calculation(self, selector_instance, mock_dependencies):
        """Test score calculation logic."""
        heur_data = {
            'sections_presence': {'summary': True, 'issues': True, 'suggestions': True},
            'bullet_points': 8,
            'length_words': 150,
            'mentions_bug': True,
            'mentions_suggest': True
        }
        meta_data = {
            'clarity': 9,
            'usefulness': 8,
            'depth': 7,
            'actionability': 8,
            'positivity': 6
        }
        
        with patch('iterative_prompt_selector.heuristic_metrics', return_value=heur_data), \
             patch('iterative_prompt_selector.meta_evaluate', return_value=(meta_data, "text")):
            
            score, _, _ = selector_instance.evaluate_review("diff", "review", "static", "context")
            
            assert isinstance(score, float)
            assert score > 0
    
    def test_evaluation_with_short_review(self, selector_instance, mock_dependencies):
        """Test evaluation with very short review."""
        heur_data = {
            'sections_presence': {},
            'bullet_points': 0,
            'length_words': 20,
            'mentions_bug': False,
            'mentions_suggest': False
        }
        
        with patch('iterative_prompt_selector.heuristic_metrics', return_value=heur_data), \
             patch('iterative_prompt_selector.meta_evaluate', mock_dependencies['meta_evaluate']):
            
            score, _, _ = selector_instance.evaluate_review("diff", "short review", "static", "context")
            
            assert isinstance(score, float)
    
    def test_evaluation_with_long_review(self, selector_instance, mock_dependencies):
        """Test evaluation with very long review."""
        heur_data = {
            'sections_presence': {'summary': True, 'issues': True},
            'bullet_points': 15,
            'length_words': 1500,
            'mentions_bug': True,
            'mentions_suggest': True
        }
        
        with patch('iterative_prompt_selector.heuristic_metrics', return_value=heur_data), \
             patch('iterative_prompt_selector.meta_evaluate', mock_dependencies['meta_evaluate']):
            
            score, _, _ = selector_instance.evaluate_review("diff", "x" * 10000, "static", "context")
            
            assert isinstance(score, float)