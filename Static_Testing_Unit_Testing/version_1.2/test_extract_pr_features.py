"""
Test suite for extract_pr_features method.
Tests feature extraction from PR diffs.
"""

import pytest
from iterative_prompt_selector import IterativePromptSelector


class TestExtractPRFeatures:
    """Test suite for PR feature extraction."""

    @pytest.fixture
    def selector(self):
        """Create selector instance for testing."""
        return IterativePromptSelector()

    def test_extract_features_basic_python_file(self, selector):
        """Test feature extraction from basic Python diff."""
        diff = """diff --git a/test.py b/test.py
+import numpy as np
+def calculate():
+    # Calculate sum
+    return sum([1, 2, 3])
"""
        features = selector.extract_pr_features(diff)
        
        assert features['num_files'] == 1
        assert features['has_imports'] == 1
        assert features['has_functions'] == 1
        assert features['has_comments'] == 1
        assert features['is_python'] == 1

    def test_extract_features_empty_diff(self, selector):
        """Test feature extraction from empty diff."""
        features = selector.extract_pr_features("")
        
        assert features['num_lines'] == 1  # Empty string has 1 line
        assert features['num_files'] == 0
        assert features['additions'] == 0
        assert features['deletions'] == 0

    def test_extract_features_multiple_files(self, selector):
        """Test feature extraction with multiple files."""
        diff = """diff --git a/file1.py b/file1.py
+import os
diff --git a/file2.js b/file2.js
+function test() {}
diff --git a/file3.java b/file3.java
+public class Test {}
"""
        features = selector.extract_pr_features(diff)
        
        assert features['num_files'] == 3
        assert features['is_python'] == 1
        assert features['is_js'] == 1
        assert features['is_java'] == 1

    def test_extract_features_test_file_detection(self, selector):
        """Test detection of test files."""
        diff = """diff --git a/test_module.py b/test_module.py
+import unittest
+class TestCase(unittest.TestCase):
+    pass
"""
        features = selector.extract_pr_features(diff)
        
        assert features['has_test'] == 1

    def test_extract_features_documentation_detection(self, selector):
        """Test detection of documentation."""
        diff = """diff --git a/README.md b/README.md
+# Documentation
+This is a readme file
"""
        features = selector.extract_pr_features(diff)
        
        assert features['has_docs'] == 1

    def test_extract_features_config_file_detection(self, selector):
        """Test detection of config files."""
        diff = """diff --git a/config.json b/config.json
+{"setting": "value"}
"""
        features = selector.extract_pr_features(diff)
        
        assert features['has_config'] == 1

    def test_extract_features_additions_and_deletions(self, selector):
        """Test counting of additions and deletions."""
        diff = """diff --git a/file.py b/file.py
+added line 1
+added line 2
-deleted line 1
+added line 3
"""
        features = selector.extract_pr_features(diff)
        
        assert features['additions'] == 3
        assert features['deletions'] == 1
        assert features['net_changes'] == 2

    def test_extract_features_multiline_comment_detection(self, selector):
        """Test detection of multiline comments."""
        diff = """diff --git a/file.py b/file.py
+/*
+ * Multiline comment
+ */
"""
        features = selector.extract_pr_features(diff)
        
        assert features['has_comments'] == 1

    def test_extract_features_no_language_match(self, selector):
        """Test diff with no recognized language."""
        diff = """diff --git a/file.txt b/file.txt
+some text
"""
        features = selector.extract_pr_features(diff)
        
        assert features['is_python'] == 0
        assert features['is_js'] == 0
        assert features['is_java'] == 0

    def test_extract_features_special_characters(self, selector):
        """Test diff with special characters and unicode."""
        diff = """diff --git a/file.py b/file.py
+# Comment with 世界 and emojis 🚀
+def test():
+    pass
"""
        features = selector.extract_pr_features(diff)
        
        assert features['has_comments'] == 1
        assert features['has_functions'] == 1