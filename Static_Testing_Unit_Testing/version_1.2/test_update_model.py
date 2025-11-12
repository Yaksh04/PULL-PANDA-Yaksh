"""
Test suite for update_model method.
Tests model training and retraining logic.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from iterative_prompt_selector import IterativePromptSelector


class TestUpdateModel:
    """Test suite for model updating."""

    @pytest.fixture
    def selector(self):
        """Create selector instance for testing."""
        return IterativePromptSelector()

    def test_update_model_first_sample(self, selector):
        """Test adding first training sample."""
        features_vector = np.array([100, 5, 50, 20, 30, 1, 1, 1, 0, 0, 0, 1, 0, 0])
        prompt_name = selector.prompt_names[0]
        score = 7.5
        
        selector.update_model(features_vector, prompt_name, score)
        
        assert len(selector.feature_history) == 1
        assert len(selector.prompt_history) == 1
        assert len(selector.score_history) == 1
        assert selector.score_history[0] == 7.5
        assert selector.is_trained == False  # Not enough samples yet

    def test_update_model_reaches_min_samples(self, selector):
        """Test model training when reaching minimum samples."""
        features_vector = np.array([100, 5, 50, 20, 30, 1, 1, 1, 0, 0, 0, 1, 0, 0])
        
        # Add minimum samples
        for i in range(selector.min_samples_for_training):
            selector.update_model(
                features_vector * (i + 1),
                selector.prompt_names[i % len(selector.prompt_names)],
                7.0 + i * 0.5
            )
        
        assert len(selector.feature_history) == selector.min_samples_for_training
        assert selector.is_trained == True

    def test_update_model_retraining(self, selector):
        """Test model retraining with additional samples."""
        features_vector = np.array([50, 2, 10, 5, 5, 0, 1, 1, 0, 0, 0, 1, 0, 0])
        
        # Initial training
        for i in range(6):
            selector.update_model(
                features_vector * (i + 1),
                selector.prompt_names[i % len(selector.prompt_names)],
                6.0 + i
            )
        
        initial_count = len(selector.feature_history)
        
        # Add more samples
        selector.update_model(features_vector * 10, selector.prompt_names[0], 9.5)
        
        assert len(selector.feature_history) == initial_count + 1
        assert selector.is_trained == True

    def test_update_model_training_failure_value_error(self, selector):
        """Test handling of ValueError during training."""
        features_vector = np.array([100, 5, 50, 20, 30, 1, 1, 1, 0, 0, 0, 1, 0, 0])
        
        # Add samples to reach min_samples
        for i in range(selector.min_samples_for_training - 1):
            selector.update_model(
                features_vector,
                selector.prompt_names[0],
                7.0
            )
        
        # Mock model.fit to raise ValueError
        with patch.object(selector.model, 'fit', side_effect=ValueError("Invalid data")):
            selector.update_model(features_vector, selector.prompt_names[0], 8.0)
            
            # Should have data stored but is_trained should be False
            assert len(selector.feature_history) == selector.min_samples_for_training
            assert selector.is_trained == False

    def test_update_model_training_failure_runtime_error(self, selector):
        """Test handling of RuntimeError during training."""
        features_vector = np.array([50, 2, 10, 5, 5, 0, 1, 1, 0, 0, 0, 1, 0, 0])
        
        for i in range(selector.min_samples_for_training - 1):
            selector.update_model(
                features_vector,
                selector.prompt_names[0],
                6.5
            )
        
        with patch.object(selector.model, 'fit', side_effect=RuntimeError("Training failed")):
            selector.update_model(features_vector, selector.prompt_names[0], 7.0)
            
            assert selector.is_trained == False

    def test_update_model_prompt_index_mapping(self, selector):
        """Test correct mapping of prompt names to indices."""
        features_vector = np.array([100, 5, 50, 20, 30, 1, 1, 1, 0, 0, 0, 1, 0, 0])
        
        # Update with third prompt
        prompt_name = selector.prompt_names[2]
        selector.update_model(features_vector, prompt_name, 8.0)
        
        assert selector.prompt_history[0] == 2

    def test_update_model_score_accumulation(self, selector):
        """Test that scores are accumulated correctly."""
        features_vector = np.array([50, 2, 10, 5, 5, 0, 1, 1, 0, 0, 0, 1, 0, 0])
        scores = [5.0, 6.5, 7.0, 8.5, 9.0, 7.5]
        
        for i, score in enumerate(scores):
            selector.update_model(
                features_vector,
                selector.prompt_names[i % len(selector.prompt_names)],
                score
            )
        
        assert selector.score_history == scores