"""
Test suite for save_state and load_state methods.
Tests persistence and restoration of model state.
"""

import pytest
import json
import numpy as np
from unittest.mock import mock_open, patch
from iterative_prompt_selector import IterativePromptSelector


class TestSaveLoadState:
    """Test suite for state persistence."""

    @pytest.fixture
    def selector(self):
        """Create selector instance for testing."""
        return IterativePromptSelector()

    @pytest.fixture
    def sample_state(self, selector):
        """Create sample training state."""
        features = np.array([100, 5, 50, 20, 30, 1, 1, 1, 0, 0, 0, 1, 0, 0])
        for i in range(6):
            selector.update_model(
                features * (i + 1),
                selector.prompt_names[i % len(selector.prompt_names)],
                7.0 + i * 0.5
            )
        return selector

    def test_save_state_success(self, sample_state):
        """Test successful state saving."""
        m = mock_open()
        with patch('builtins.open', m):
            sample_state.save_state("test_state.json")
        
        m.assert_called_once_with("test_state.json", 'w', encoding='utf-8')
        handle = m()
        written_data = ''.join(call.args[0] for call in handle.write.call_args_list)
        state = json.loads(written_data)
        
        assert "feature_history" in state
        assert "prompt_history" in state
        assert "score_history" in state
        assert "is_trained" in state

    def test_save_state_untrained_model(self, selector):
        """Test saving state when model is untrained."""
        m = mock_open()
        with patch('builtins.open', m):
            selector.save_state("test_state.json")
        
        handle = m()
        written_data = ''.join(call.args[0] for call in handle.write.call_args_list)
        state = json.loads(written_data)
        
        assert state["is_trained"] == False
        assert state["scaler_mean"] is None
        assert state["scaler_scale"] is None

    def test_load_state_success(self, selector):
        """Test successful state loading."""
        state_data = {
            "feature_history": [[100, 5, 50, 20, 30, 1, 1, 1, 0, 0, 0, 1, 0, 0]],
            "prompt_history": [0],
            "score_history": [7.5],
            "is_trained": True,
            "scaler_mean": [50.0] * 15,
            "scaler_scale": [10.0] * 15
        }
        
        m = mock_open(read_data=json.dumps(state_data))
        with patch('builtins.open', m):
            selector.load_state("test_state.json")
        
        assert len(selector.feature_history) == 1
        assert len(selector.prompt_history) == 1
        assert len(selector.score_history) == 1
        assert selector.is_trained == True

    def test_load_state_file_not_found(self, selector):
        """Test loading when file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            selector.load_state("nonexistent.json")
        
        # Should continue with empty state
        assert len(selector.feature_history) == 0
        assert selector.is_trained == False

    def test_load_state_invalid_json(self, selector):
        """Test loading with invalid JSON."""
        m = mock_open(read_data="invalid json {")
        with patch('builtins.open', m):
            selector.load_state("bad_state.json")
        
        # Should reset to empty state
        assert len(selector.feature_history) == 0
        assert selector.is_trained == False

    def test_load_state_missing_keys(self, selector):
        """Test loading with missing required keys."""
        incomplete_state = {
            "feature_history": [],
            "prompt_history": []
            # Missing score_history and other keys
        }
        
        m = mock_open(read_data=json.dumps(incomplete_state))
        with patch('builtins.open', m):
            selector.load_state("incomplete_state.json")
        
        assert len(selector.feature_history) == 0
        assert selector.is_trained == False

    def test_load_state_invalid_data_types(self, selector):
        """Test loading with invalid data types."""
        invalid_state = {
            "feature_history": "not a list",
            "prompt_history": [0],
            "score_history": [7.5],
            "is_trained": True,
            "scaler_mean": None,
            "scaler_scale": None
        }
        
        m = mock_open(read_data=json.dumps(invalid_state))
        with patch('builtins.open', m):
            selector.load_state("invalid_state.json")
        
        assert selector.is_trained == False

    def test_save_load_roundtrip(self, sample_state):
        """Test that save and load preserve state."""
        # Save state
        state_dict = {}
        
        def mock_write(data):
            state_dict['data'] = data
        
        m_save = mock_open()
        with patch('builtins.open', m_save):
            sample_state.save_state("test.json")
        
        handle = m_save()
        written_data = ''.join(call.args[0] for call in handle.write.call_args_list)
        
        # Load into new selector
        new_selector = IterativePromptSelector()
        m_load = mock_open(read_data=written_data)
        with patch('builtins.open', m_load):
            new_selector.load_state("test.json")
        
        assert len(new_selector.feature_history) == len(sample_state.feature_history)
        assert new_selector.is_trained == sample_state.is_trained

    def test_load_state_with_scaler_restoration(self, selector):
        """Test scaler attributes are properly restored."""
        state_data = {
            "feature_history": [[100, 5, 50, 20, 30, 1, 1, 1, 0, 0, 0, 1, 0, 0]],
            "prompt_history": [0],
            "score_history": [7.5],
            "is_trained": True,
            "scaler_mean": [50.0] * 15,
            "scaler_scale": [10.0] * 15
        }
        
        m = mock_open(read_data=json.dumps(state_data))
        with patch('builtins.open', m):
            selector.load_state("test_state.json")
        
        assert hasattr(selector.scaler, 'mean_')
        assert hasattr(selector.scaler, 'scale_')
        assert len(selector.scaler.mean_) == 15