"""
Test suite for process_pr method.
Tests end-to-end PR processing workflow.
"""

import pytest
from unittest.mock import patch, Mock, mock_open
from iterative_prompt_selector import IterativePromptSelector


class TestProcessPR:
    """Test suite for PR processing."""

    @pytest.fixture
    def selector(self):
        """Create selector instance for testing."""
        return IterativePromptSelector()

    @patch('iterative_prompt_selector.fetch_pr_diff')
    @patch.object(IterativePromptSelector, 'generate_review')
    @patch.object(IterativePromptSelector, 'evaluate_review')
    @patch.object(IterativePromptSelector, 'save_results')
    def test_process_pr_success(self, mock_save, mock_eval, mock_gen, mock_fetch, selector):
        """Test successful PR processing."""
        mock_fetch.return_value = "diff --git a/test.py\n+new line"
        mock_gen.return_value = ("Great review", 1.5)
        mock_eval.return_value = (8.5, {}, {})
        
        result = selector.process_pr(123)
        
        assert result['pr_number'] == 123
        assert result['selected_prompt'] in selector.prompt_names
        assert result['review'] == "Great review"
        assert result['score'] == 8.5
        assert 'features' in result
        mock_fetch.assert_called_once()
        mock_gen.assert_called_once()
        mock_eval.assert_called_once()
        mock_save.assert_called_once()

    @patch('iterative_prompt_selector.fetch_pr_diff')
    def test_process_pr_fetch_failure(self, mock_fetch, selector):
        """Test handling of fetch failure."""
        mock_fetch.side_effect = Exception("API error")
        
        with pytest.raises(Exception):
            selector.process_pr(123)

    @patch('iterative_prompt_selector.fetch_pr_diff')
    @patch.object(IterativePromptSelector, 'extract_pr_features')
    @patch.object(IterativePromptSelector, 'select_best_prompt')
    @patch.object(IterativePromptSelector, 'generate_review')
    @patch.object(IterativePromptSelector, 'evaluate_review')
    @patch.object(IterativePromptSelector, 'save_results')
    def test_process_pr_with_custom_params(self, mock_save, mock_eval, mock_gen, 
                                            mock_select, mock_extract, mock_fetch, selector):
        """Test PR processing with custom owner/repo/token."""
        mock_fetch.return_value = "diff content"
        mock_extract.return_value = {'num_lines': 100}
        mock_select.return_value = selector.prompt_names[0]
        mock_gen.return_value = ("Review", 1.0)
        mock_eval.return_value = (7.0, {}, {})
        
        result = selector.process_pr(456, owner="custom", repo="test", token="token123")
        
        mock_fetch.assert_called_once_with("custom", "test", 456, "token123")
        assert result['pr_number'] == 456

    @patch('iterative_prompt_selector.fetch_pr_diff')
    @patch.object(IterativePromptSelector, 'generate_review')
    @patch.object(IterativePromptSelector, 'evaluate_review')
    @patch.object(IterativePromptSelector, 'update_model')
    @patch.object(IterativePromptSelector, 'save_results')
    def test_process_pr_updates_model(self, mock_save, mock_update, mock_eval, 
                                       mock_gen, mock_fetch, selector):
        """Test that model is updated after processing."""
        mock_fetch.return_value = "diff"
        mock_gen.return_value = ("Review", 1.0)
        mock_eval.return_value = (8.0, {}, {})
        
        selector.process_pr(789)
        
        mock_update.assert_called_once()
        call_args = mock_update.call_args[0]
        assert len(call_args) == 3  # features_vector, prompt_name, score

    @patch('iterative_prompt_selector.fetch_pr_diff')
    @patch.object(IterativePromptSelector, 'generate_review')
    @patch.object(IterativePromptSelector, 'evaluate_review')
    @patch.object(IterativePromptSelector, 'save_results')
    def test_process_pr_empty_diff(self, mock_save, mock_eval, mock_gen, mock_fetch, selector):
        """Test processing with empty diff."""
        mock_fetch.return_value = ""
        mock_gen.return_value = ("No changes", 0.5)
        mock_eval.return_value = (5.0, {}, {})
        
        result = selector.process_pr(999)
        
        assert result['pr_number'] == 999
        assert 'features' in result