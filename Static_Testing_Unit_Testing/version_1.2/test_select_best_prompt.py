"""
Test suite for select_best_prompt method.
Tests prompt selection logic with and without trained model.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from iterative_prompt_selector import IterativePromptSelector


class TestSelectBestPrompt:
    """Test suite for prompt selection."""

    @pytest.fixture
    def selector(self):
        """Create selector instance for testing."""
        return IterativePromptSelector()

    def test_select_prompt_untrained_round_robin(self, selector):
        """Test round-robin selection when model is untrained."""
        features_vector = np.array([100, 5, 50, 20, 30, 1, 1, 1, 0, 0, 0, 1, 0, 0])
        
        # First call should return first prompt
        prompt1 = selector.select_best_prompt(features_vector)
        assert prompt1 == selector.prompt_names[0]
        
        # Add one sample to history
        selector.feature_history.append(features_vector)
        
        # Second call should return second prompt
        prompt2 = selector.select_best_prompt(features_vector)
        assert prompt2 == selector.prompt_names[1]

    def test_select_prompt_insufficient_training_data(self, selector):
        """Test selection with insufficient training data."""
        features_vector = np.array([50, 2, 10, 5, 5, 0, 1, 1, 0, 0, 0, 1, 0, 0])
        
        # Add some samples but less than min_samples_for_training
        for i in range(3):
            selector.feature_history.append(features_vector)
        
        selector.is_trained = False
        
        # Should still use round-robin
        prompt = selector.select_best_prompt(features_vector)
        assert prompt in selector.prompt_names

    def test_select_prompt_with_trained_model(self, selector):
        """Test selection with trained model."""
        features_vector = np.array([100, 5, 50, 20, 30, 1, 1, 1, 0, 0, 0, 1, 0, 0])
        
        # Setup trained state
        selector.is_trained = True
        for i in range(6):
            selector.feature_history.append(features_vector * (i + 1))
        
        # Mock the model prediction
        selector.model.predict = Mock(return_value=np.array([5.0, 7.5, 6.0, 4.5, 8.0, 5.5, 6.5]))
        
        # Should return prompt with highest predicted score
        prompt = selector.select_best_prompt(features_vector)
        assert prompt == selector.prompt_names[4]  # Index 4 has score 8.0

    def test_select_prompt_model_prediction_failure(self, selector):
        """Test fallback when model prediction fails."""
        features_vector = np.array([100, 5, 50, 20, 30, 1, 1, 1, 0, 0, 0, 1, 0, 0])
        
        selector.is_trained = True
        for i in range(6):
            selector.feature_history.append(features_vector)
        
        # Mock model to raise error
        selector.model.predict = Mock(side_effect=ValueError("Prediction error"))
        
        # Should fallback to first prompt
        prompt = selector.select_best_prompt(features_vector)
        assert prompt == selector.prompt_names[0]

    def test_select_prompt_index_error_handling(self, selector):
        """Test handling of IndexError during selection."""
        features_vector = np.array([100, 5, 50, 20, 30, 1, 1, 1, 0, 0, 0, 1, 0, 0])
        
        selector.is_trained = True
        for i in range(6):
            selector.feature_history.append(features_vector)
        
        # Mock model to raise IndexError
        selector.model.predict = Mock(side_effect=IndexError("Index out of range"))
        
        prompt = selector.select_best_prompt(features_vector)
        assert prompt == selector.prompt_names[0]

    def test_select_prompt_all_equal_scores(self, selector):
        """Test selection when all prompts have equal predicted scores."""
        features_vector = np.array([50, 2, 10, 5, 5, 0, 1, 1, 0, 0, 0, 1, 0, 0])
        
        selector.is_trained = True
        for i in range(6):
            selector.feature_history.append(features_vector)
        
        # All scores equal
        selector.model.predict = Mock(return_value=np.array([5.0] * len(selector.prompt_names)))
        
        # Should return first prompt (argmax returns first index for ties)
        prompt = selector.select_best_prompt(features_vector)
        assert prompt == selector.prompt_names[0]