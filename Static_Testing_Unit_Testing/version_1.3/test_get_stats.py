"""
Updated test suite for get_stats.
Each test labeled KEEP / OBSOLETE / NEW.
"""

import pytest
import numpy as np
import unittest
from unittest.mock import patch
from online_estimator_version import IterativePromptSelector


class TestGetStats:
    """Tests for get_stats method."""
    
    def test_get_stats_empty_history(self, selector_instance):
        """Test get_stats with no training history."""
        stats = selector_instance.get_stats()
        
        assert stats['training_samples'] == 0
        assert stats['average_score'] == 0
        assert stats['unique_prompts_used'] == 0
    
    def test_get_stats_with_data(self, selector_instance):
        """Test get_stats with training data."""
        selector_instance.feature_history = [np.array([1]*14), np.array([2]*14)]
        selector_instance.prompt_history = [0, 1]
        selector_instance.score_history = [7.0, 8.5]
        selector_instance.sample_count = 2
        
        stats = selector_instance.get_stats()
        
        assert stats['training_samples'] == 2
        assert stats['average_score'] == 7.75
        assert stats['unique_prompts_used'] == 2
    
    def test_get_stats_prompt_distribution(self, selector_instance):
        """Test prompt distribution calculation."""
        selector_instance.prompt_history = [0, 0, 1, 2, 1]
        selector_instance.sample_count = 5
        selector_instance.score_history = [7, 8, 6, 9, 7]
        
        stats = selector_instance.get_stats()
        
        dist = stats['prompt_distribution']
        assert dist['detailed'] == 2
        assert dist['concise'] == 2
        assert dist['security'] == 1
    
    def test_get_stats_scaler_status(self, selector_instance):
        """Test scaler fitted status in stats."""
        selector_instance.is_scaler_fitted = True
        
        stats = selector_instance.get_stats()
        
        assert stats['is_scaler_fitted'] is True
