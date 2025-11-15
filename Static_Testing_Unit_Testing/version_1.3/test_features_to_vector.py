"""
Test suite for features_to_vector method.
Tests conversion of feature dictionaries to numerical vectors.
"""

import pytest
import numpy as np
import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
from online_estimator_version import IterativePromptSelector


class TestFeaturesToVector:
    """Tests for features_to_vector method."""
    
    def test_complete_features_conversion(self, selector_instance):
        """Test conversion of complete feature dict to vector."""
        features = {
            'num_lines': 100,
            'num_files': 5,
            'additions': 50,
            'deletions': 20,
            'net_changes': 30,
            'has_comments': 1,
            'has_functions': 1,
            'has_imports': 1,
            'has_test': 0,
            'has_docs': 0,
            'has_config': 0,
            'is_python': 1,
            'is_js': 0,
            'is_java': 0
        }
        vector = selector_instance.features_to_vector(features)
        
        assert len(vector) == 14
        assert vector[0] == 100
        assert vector[1] == 5
        assert isinstance(vector, np.ndarray)
    
    def test_missing_features_default_to_zero(self, selector_instance):
        """Test that missing features default to zero."""
        features = {'num_lines': 50}
        vector = selector_instance.features_to_vector(features)
        
        assert len(vector) == 14
        assert vector[0] == 50
        assert vector[1] == 0
        assert np.sum(vector[2:]) == 0
    
    def test_empty_features_dict(self, selector_instance):
        """Test conversion of empty features dict."""
        vector = selector_instance.features_to_vector({})
        
        assert len(vector) == 14
        assert np.all(vector == 0)
    
    def test_extra_features_ignored(self, selector_instance):
        """Test that extra features in dict are ignored."""
        features = {
            'num_lines': 10,
            'extra_feature': 999,
            'another_extra': 'ignored'
        }
        vector = selector_instance.features_to_vector(features)
        
        assert len(vector) == 14
        assert vector[0] == 10
