"""
Test suite for features_to_vector method.
Tests conversion of feature dictionaries to numerical vectors.
"""

import pytest
import numpy as np
from iterative_prompt_selector import IterativePromptSelector


class TestFeaturesToVector:
    """Test suite for features to vector conversion."""

    @pytest.fixture
    def selector(self):
        """Create selector instance for testing."""
        return IterativePromptSelector()

    def test_features_to_vector_complete_features(self, selector):
        """Test conversion with all features present."""
        features = {
            'num_lines': 100,
            'num_files': 5,
            'additions': 50,
            'deletions': 20,
            'net_changes': 30,
            'has_comments': 1,
            'has_functions': 1,
            'has_imports': 1,
            'has_test': 1,
            'has_docs': 0,
            'has_config': 0,
            'is_python': 1,
            'is_js': 0,
            'is_java': 0
        }
        
        vector = selector.features_to_vector(features)
        
        assert isinstance(vector, np.ndarray)
        assert len(vector) == 14
        assert vector[0] == 100  # num_lines
        assert vector[1] == 5    # num_files
        assert vector[5] == 1    # has_comments

    def test_features_to_vector_missing_features(self, selector):
        """Test conversion with missing features (should default to 0)."""
        features = {
            'num_lines': 50,
            'additions': 10
        }
        
        vector = selector.features_to_vector(features)
        
        assert len(vector) == 14
        assert vector[0] == 50  # num_lines
        assert vector[1] == 0   # num_files (missing)
        assert vector[2] == 10  # additions

    def test_features_to_vector_empty_features(self, selector):
        """Test conversion with empty feature dict."""
        features = {}
        
        vector = selector.features_to_vector(features)
        
        assert len(vector) == 14
        assert np.all(vector == 0)

    def test_features_to_vector_extra_features_ignored(self, selector):
        """Test that extra features are ignored."""
        features = {
            'num_lines': 100,
            'extra_feature': 999,  # Should be ignored
            'another_extra': 'value'
        }
        
        vector = selector.features_to_vector(features)
        
        assert len(vector) == 14
        assert vector[0] == 100

    def test_features_to_vector_correct_order(self, selector):
        """Test that features are in correct order."""
        features = {
            'is_java': 1,
            'num_lines': 10,
            'has_test': 1
        }
        
        vector = selector.features_to_vector(features)
        
        # Verify order matches expected feature_order
        assert vector[0] == 10  # num_lines is first
        assert vector[8] == 1   # has_test
        assert vector[13] == 1  # is_java is last