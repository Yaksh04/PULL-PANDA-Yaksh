"""
Test suite for extract_pr_features method.
Tests feature extraction from PR diffs.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
from online_estimator_version import IterativePromptSelector


class TestExtractPRFeatures:
    """Tests for extract_pr_features method."""
    
    def test_basic_diff_features(self, selector_instance):
        """Test feature extraction from basic diff."""
        diff = "diff --git a/file.py b/file.py\n+added line\n-removed line"
        features = selector_instance.extract_pr_features(diff)
        
        assert 'num_lines' in features
        assert 'num_files' in features
        assert 'additions' in features
        assert 'deletions' in features
        assert features['num_files'] == 1
    
    def test_empty_diff(self, selector_instance):
        """Test feature extraction from empty diff."""
        features = selector_instance.extract_pr_features("")
        
        assert features['num_lines'] == 1  # Empty string has 1 line
        assert features['num_files'] == 0
        assert features['additions'] == 0
        assert features['deletions'] == 0
    
    def test_multiple_files_detection(self, selector_instance):
        """Test detection of multiple files in diff."""
        diff = """diff --git a/file1.py b/file1.py
+code
diff --git a/file2.js b/file2.js
+more code"""
        features = selector_instance.extract_pr_features(diff)
        
        assert features['num_files'] == 2
    
    def test_python_file_detection(self, selector_instance):
        """Test Python file detection."""
        diff = "diff --git a/script.py b/script.py"
        features = selector_instance.extract_pr_features(diff)
        
        assert features['is_python'] == 1
        assert features['is_js'] == 0
        assert features['is_java'] == 0
    
    def test_javascript_file_detection(self, selector_instance):
        """Test JavaScript file detection."""
        diff = "diff --git a/app.js b/app.js"
        features = selector_instance.extract_pr_features(diff)
        
        assert features['is_js'] == 1
        assert features['is_python'] == 0
    
    def test_typescript_file_detection(self, selector_instance):
        """Test TypeScript file detection."""
        diff = "diff --git a/component.ts b/component.ts"
        features = selector_instance.extract_pr_features(diff)
        
        assert features['is_js'] == 1
    
    def test_java_file_detection(self, selector_instance):
        """Test Java file detection."""
        diff = "diff --git a/Main.java b/Main.java"
        features = selector_instance.extract_pr_features(diff)
        
        assert features['is_java'] == 1
    
    def test_function_detection(self, selector_instance):
        """Test function definition detection."""
        diff = "def my_function():\n    pass"
        features = selector_instance.extract_pr_features(diff)
        
        assert features['has_functions'] == 1
    
    def test_import_detection(self, selector_instance):
        """Test import statement detection."""
        diff = "import os\nfrom datetime import datetime"
        features = selector_instance.extract_pr_features(diff)
        
        assert features['has_imports'] == 1
    
    def test_comment_detection(self, selector_instance):
        """Test comment detection."""
        diff = "# This is a comment\n// Another comment\n/* Block comment */"
        features = selector_instance.extract_pr_features(diff)
        
        assert features['has_comments'] == 1
    
    def test_test_file_detection(self, selector_instance):
        """Test test file detection."""
        diff = "diff --git a/test_module.py b/test_module.py"
        features = selector_instance.extract_pr_features(diff)
        
        assert features['has_test'] == 1
    
    def test_documentation_detection(self, selector_instance):
        """Test documentation detection."""
        diff = "README.md updated with new documentation"
        features = selector_instance.extract_pr_features(diff)
        
        assert features['has_docs'] == 1
    
    def test_config_file_detection(self, selector_instance):
        """Test config file detection."""
        diff = "diff --git a/config.json b/config.json"
        features = selector_instance.extract_pr_features(diff)
        
        assert features['has_config'] == 1
    
    def test_net_changes_calculation(self, selector_instance):
        """Test net changes calculation."""
        diff = "+line1\n+line2\n+line3\n-line4"
        features = selector_instance.extract_pr_features(diff)
        
        assert features['additions'] == 3
        assert features['deletions'] == 1
        assert features['net_changes'] == 2
    
    def test_large_diff_handling(self, selector_instance):
        """Test handling of large diff with many lines."""
        diff = "\n".join([f"+line{i}" for i in range(1000)])
        features = selector_instance.extract_pr_features(diff)
        
        assert features['num_lines'] == 1000
        assert features['additions'] == 1000
