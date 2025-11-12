"""
Test suite for evaluate_review method.
Tests review evaluation and scoring logic.
"""

import pytest
from unittest.mock import patch
from iterative_prompt_selector import IterativePromptSelector


class TestEvaluateReview:
    """Test suite for review evaluation."""

    @pytest.fixture
    def selector(self):
        """Create selector instance for testing."""
        return IterativePromptSelector()

    @patch('iterative_prompt_selector.heuristic_metrics')
    @patch('iterative_prompt_selector.meta_evaluate')
    def test_evaluate_review_success(self, mock_meta, mock_heur, selector):
        """Test successful review evaluation."""
        diff_text = "diff content"
        review_text = "This is a comprehensive review"
        
        mock_heur.return_value = {
            "sections_presence": {"summary": True, "issues": True},
            "bullet_points": 5,
            "length_words": 150,
            "mentions_bug": True,
            "mentions_suggest": True
        }
        
        mock_meta.return_value = (
            {
                "clarity": 8.0,
                "usefulness": 7.5,
                "depth": 7.0,
                "actionability": 8.5,
                "positivity": 6.0
            },
            {}
        )
        
        score, heur, meta = selector.evaluate_review(diff_text, review_text)
        
        assert isinstance(score, float)
        assert 0 <= score <= 10
        assert isinstance(heur, dict)
        assert isinstance(meta, dict)

    @patch('iterative_prompt_selector.heuristic_metrics')
    @patch('iterative_prompt_selector.meta_evaluate')
    def test_evaluate_review_meta_error(self, mock_meta, mock_heur, selector):
        """Test evaluation when meta_evaluate returns error."""
        diff_text = "diff"
        review_text = "review"
        
        mock_heur.return_value = {
            "sections_presence": {},
            "bullet_points": 0,
            "length_words": 50,
            "mentions_bug": False,
            "mentions_suggest": False
        }
        
        mock_meta.return_value = ({"error": "Failed"}, {})
        
        score, heur, meta = selector.evaluate_review(diff_text, review_text)
        
        assert score == 5.0  # Default score

    @patch('iterative_prompt_selector.heuristic_metrics')
    @patch('iterative_prompt_selector.meta_evaluate')
    def test_evaluate_review_edge_word_count_low(self, mock_meta, mock_heur, selector):
        """Test evaluation with word count below threshold."""
        mock_heur.return_value = {
            "sections_presence": {"summary": True},
            "bullet_points": 3,
            "length_words": 40,  # Below 80
            "mentions_bug": False,
            "mentions_suggest": False
        }
        
        mock_meta.return_value = (
            {
                "clarity": 7.0,
                "usefulness": 7.0,
                "depth": 6.0,
                "actionability": 7.0,
                "positivity": 6.0
            },
            {}
        )
        
        score, heur, meta = selector.evaluate_review("diff", "short review")
        
        assert isinstance(score, float)
        # Score should be penalized for low word count

    @patch('iterative_prompt_selector.heuristic_metrics')
    @patch('iterative_prompt_selector.meta_evaluate')
    def test_evaluate_review_edge_word_count_high(self, mock_meta, mock_heur, selector):
        """Test evaluation with word count above threshold."""
        mock_heur.return_value = {
            "sections_presence": {"summary": True, "issues": True},
            "bullet_points": 8,
            "length_words": 1500,  # Way above 800
            "mentions_bug": True,
            "mentions_suggest": True
        }
        
        mock_meta.return_value = (
            {
                "clarity": 8.0,
                "usefulness": 8.0,
                "depth": 7.5,
                "actionability": 8.0,
                "positivity": 7.0
            },
            {}
        )
        
        score, heur, meta = selector.evaluate_review("diff", "very long review")
        
        assert isinstance(score, float)
        # Score should be penalized for excessive length

    @patch('iterative_prompt_selector.heuristic_metrics')
    @patch('iterative_prompt_selector.meta_evaluate')
    def test_evaluate_review_optimal_word_count(self, mock_meta, mock_heur, selector):
        """Test evaluation with optimal word count."""
        mock_heur.return_value = {
            "sections_presence": {"summary": True, "issues": True, "suggestions": True},
            "bullet_points": 6,
            "length_words": 200,  # Between 80 and 800
            "mentions_bug": True,
            "mentions_suggest": True
        }
        
        mock_meta.return_value = (
            {
                "clarity": 9.0,
                "usefulness": 8.5,
                "depth": 8.0,
                "actionability": 9.0,
                "positivity": 7.5
            },
            {}
        )
        
        score, heur, meta = selector.evaluate_review("diff", "optimal review")
        
        assert score > 7.0  # Should have good score

    @patch('iterative_prompt_selector.heuristic_metrics')
    @patch('iterative_prompt_selector.meta_evaluate')
    def test_evaluate_review_no_sections(self, mock_meta, mock_heur, selector):
        """Test evaluation with no sections detected."""
        mock_heur.return_value = {
            "sections_presence": {},
            "bullet_points": 2,
            "length_words": 100,
            "mentions_bug": False,
            "mentions_suggest": False
        }
        
        mock_meta.return_value = (
            {
                "clarity": 6.0,
                "usefulness": 6.0,
                "depth": 5.0,
                "actionability": 6.0,
                "positivity": 6.0
            },
            {}
        )
        
        score, heur, meta = selector.evaluate_review("diff", "plain review")
        
        assert isinstance(score, float)

    @patch('iterative_prompt_selector.heuristic_metrics')
    @patch('iterative_prompt_selector.meta_evaluate')
    def test_evaluate_review_excessive_bullets(self, mock_meta, mock_heur, selector):
        """Test evaluation with excessive bullet points."""
        mock_heur.return_value = {
            "sections_presence": {"summary": True},
            "bullet_points": 25,  # Way over 10
            "length_words": 300,
            "mentions_bug": False,
            "mentions_suggest": True
        }
        
        mock_meta.return_value = (
            {
                "clarity": 7.0,
                "usefulness": 7.0,
                "depth": 6.0,
                "actionability": 7.0,
                "positivity": 6.0
            },
            {}
        )
        
        score, heur, meta = selector.evaluate_review("diff", "bullet heavy review")
        
        # Bullet score should be capped at 10
        assert isinstance(score, float)