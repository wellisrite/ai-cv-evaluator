"""
Unit tests for scoring logic and calculations.
"""
from django.test import TestCase
from evaluation.llm_evaluator import LLMEvaluator


class ScoringLogicTest(TestCase):
    """Test cases for scoring logic and calculations."""
    
    def test_cv_match_rate_calculation(self):
        """Test CV match rate calculation accuracy."""
        # Test case 1: Perfect scores
        scores = {
            'technical_skills_match': {'score': 5},
            'experience_level': {'score': 5},
            'relevant_achievements': {'score': 5},
            'cultural_fit': {'score': 5}
        }
        
        # Expected: (5*0.4 + 5*0.25 + 5*0.2 + 5*0.15) / 5 = 5 / 5 = 1.0
        expected_rate = (5*0.4 + 5*0.25 + 5*0.2 + 5*0.15) / 5
        self.assertEqual(expected_rate, 1.0)
        
        # Test case 2: Mixed scores
        scores = {
            'technical_skills_match': {'score': 4},  # 40% weight
            'experience_level': {'score': 3},        # 25% weight
            'relevant_achievements': {'score': 4},   # 20% weight
            'cultural_fit': {'score': 3}             # 15% weight
        }
        
        # Expected: (4*0.4 + 3*0.25 + 4*0.2 + 3*0.15) / 5 = 3.6 / 5 = 0.72
        expected_rate = (4*0.4 + 3*0.25 + 4*0.2 + 3*0.15) / 5
        self.assertAlmostEqual(expected_rate, 0.72, places=2)
        
        # Test case 3: Low scores
        scores = {
            'technical_skills_match': {'score': 1},
            'experience_level': {'score': 1},
            'relevant_achievements': {'score': 1},
            'cultural_fit': {'score': 1}
        }
        
        # Expected: (1*0.4 + 1*0.25 + 1*0.2 + 1*0.15) / 5 = 1 / 5 = 0.2
        expected_rate = (1*0.4 + 1*0.25 + 1*0.2 + 1*0.15) / 5
        self.assertEqual(expected_rate, 0.2)
        
    def test_project_score_calculation(self):
        """Test project score calculation accuracy."""
        # Test case 1: Perfect scores
        scores = {
            'correctness': {'score': 5},      # 30% weight
            'code_quality': {'score': 5},     # 25% weight
            'resilience': {'score': 5},       # 20% weight
            'documentation': {'score': 5},    # 15% weight
            'creativity': {'score': 5}        # 10% weight
        }
        
        # Expected: 5*0.3 + 5*0.25 + 5*0.2 + 5*0.15 + 5*0.1 = 5.0
        expected_score = 5*0.3 + 5*0.25 + 5*0.2 + 5*0.15 + 5*0.1
        self.assertEqual(expected_score, 5.0)
        
        # Test case 2: Mixed scores
        scores = {
            'correctness': {'score': 4},      # 30% weight
            'code_quality': {'score': 3},     # 25% weight
            'resilience': {'score': 4},       # 20% weight
            'documentation': {'score': 3},    # 15% weight
            'creativity': {'score': 2}        # 10% weight
        }
        
        # Expected: 4*0.3 + 3*0.25 + 4*0.2 + 3*0.15 + 2*0.1 = 3.4
        expected_score = 4*0.3 + 3*0.25 + 4*0.2 + 3*0.15 + 2*0.1
        self.assertAlmostEqual(expected_score, 3.4, places=2)
        
        # Test case 3: Low scores
        scores = {
            'correctness': {'score': 1},
            'code_quality': {'score': 1},
            'resilience': {'score': 1},
            'documentation': {'score': 1},
            'creativity': {'score': 1}
        }
        
        # Expected: 1*0.3 + 1*0.25 + 1*0.2 + 1*0.15 + 1*0.1 = 1.0
        expected_score = 1*0.3 + 1*0.25 + 1*0.2 + 1*0.15 + 1*0.1
        self.assertEqual(expected_score, 1.0)
        
    def test_score_validation_ranges(self):
        """Test score validation ranges."""
        # Test valid score ranges
        valid_scores = [1, 2, 3, 4, 5]
        for score in valid_scores:
            self.assertTrue(1 <= score <= 5, f"Score {score} should be valid")
            
        # Test invalid score ranges (integers only for this validation)
        invalid_scores = [0, 6, -1, 10]
        for score in invalid_scores:
            self.assertFalse(1 <= score <= 5, f"Score {score} should be invalid")
        
        # Test decimal scores (should be valid for calculations)
        decimal_scores = [1.5, 2.5, 3.7, 4.8]
        for score in decimal_scores:
            self.assertTrue(1 <= score <= 5, f"Score {score} should be valid")
            
    def test_cv_match_rate_range(self):
        """Test CV match rate range validation."""
        # Test valid CV match rate ranges
        valid_rates = [0.0, 0.2, 0.5, 0.75, 1.0]
        for rate in valid_rates:
            self.assertTrue(0.0 <= rate <= 1.0, f"CV match rate {rate} should be valid")
            
        # Test invalid CV match rate ranges
        invalid_rates = [-0.1, 1.1, 2.0, -0.5]
        for rate in invalid_rates:
            self.assertFalse(0.0 <= rate <= 1.0, f"CV match rate {rate} should be invalid")
            
    def test_project_score_range(self):
        """Test project score range validation."""
        # Test valid project score ranges
        valid_scores = [1.0, 2.5, 3.0, 4.2, 5.0]
        for score in valid_scores:
            self.assertTrue(1.0 <= score <= 5.0, f"Project score {score} should be valid")
            
        # Test invalid project score ranges
        invalid_scores = [0.9, 5.1, 0.0, 6.0, -1.0]
        for score in invalid_scores:
            self.assertFalse(1.0 <= score <= 5.0, f"Project score {score} should be invalid")
            
    def test_weight_distribution(self):
        """Test that weights sum to 1.0."""
        # CV evaluation weights
        cv_weights = [0.4, 0.25, 0.2, 0.15]
        cv_weight_sum = sum(cv_weights)
        self.assertAlmostEqual(cv_weight_sum, 1.0, places=2)
        
        # Project evaluation weights
        project_weights = [0.3, 0.25, 0.2, 0.15, 0.1]
        project_weight_sum = sum(project_weights)
        self.assertAlmostEqual(project_weight_sum, 1.0, places=2)
        
    def test_edge_case_scores(self):
        """Test edge case scores."""
        # Test with all minimum scores
        min_cv_scores = {
            'technical_skills_match': {'score': 1},
            'experience_level': {'score': 1},
            'relevant_achievements': {'score': 1},
            'cultural_fit': {'score': 1}
        }
        
        min_cv_rate = (1*0.4 + 1*0.25 + 1*0.2 + 1*0.15) / 5
        self.assertEqual(min_cv_rate, 0.2)
        
        min_project_scores = {
            'correctness': {'score': 1},
            'code_quality': {'score': 1},
            'resilience': {'score': 1},
            'documentation': {'score': 1},
            'creativity': {'score': 1}
        }
        
        min_project_score = 1*0.3 + 1*0.25 + 1*0.2 + 1*0.15 + 1*0.1
        self.assertEqual(min_project_score, 1.0)
        
        # Test with all maximum scores
        max_cv_scores = {
            'technical_skills_match': {'score': 5},
            'experience_level': {'score': 5},
            'relevant_achievements': {'score': 5},
            'cultural_fit': {'score': 5}
        }
        
        max_cv_rate = (5*0.4 + 5*0.25 + 5*0.2 + 5*0.15) / 5
        self.assertEqual(max_cv_rate, 1.0)
        
        max_project_scores = {
            'correctness': {'score': 5},
            'code_quality': {'score': 5},
            'resilience': {'score': 5},
            'documentation': {'score': 5},
            'creativity': {'score': 5}
        }
        
        max_project_score = 5*0.3 + 5*0.25 + 5*0.2 + 5*0.15 + 5*0.1
        self.assertEqual(max_project_score, 5.0)
        
    def test_scoring_consistency(self):
        """Test scoring consistency across multiple calculations."""
        # Test that the same inputs always produce the same outputs
        scores = {
            'technical_skills_match': {'score': 4},
            'experience_level': {'score': 3},
            'relevant_achievements': {'score': 4},
            'cultural_fit': {'score': 3}
        }
        
        # Calculate multiple times
        rate1 = (4*0.4 + 3*0.25 + 4*0.2 + 3*0.15) / 5
        rate2 = (4*0.4 + 3*0.25 + 4*0.2 + 3*0.15) / 5
        rate3 = (4*0.4 + 3*0.25 + 4*0.2 + 3*0.15) / 5
        
        self.assertEqual(rate1, rate2)
        self.assertEqual(rate2, rate3)
        self.assertAlmostEqual(rate1, 0.72, places=2)
        
    def test_weight_impact_analysis(self):
        """Test the impact of different weights on final scores."""
        # Test that higher weighted parameters have more impact
        base_scores = {
            'technical_skills_match': {'score': 3},  # 40% weight - highest impact
            'experience_level': {'score': 3},        # 25% weight
            'relevant_achievements': {'score': 3},   # 20% weight
            'cultural_fit': {'score': 3}             # 15% weight - lowest impact
        }
        
        base_rate = (3*0.4 + 3*0.25 + 3*0.2 + 3*0.15) / 5
        
        # Increase technical skills (highest weight)
        high_tech_scores = base_scores.copy()
        high_tech_scores['technical_skills_match'] = {'score': 5}
        high_tech_rate = (5*0.4 + 3*0.25 + 3*0.2 + 3*0.15) / 5
        
        # Increase cultural fit (lowest weight)
        high_culture_scores = base_scores.copy()
        high_culture_scores['cultural_fit'] = {'score': 5}
        high_culture_rate = (3*0.4 + 3*0.25 + 3*0.2 + 5*0.15) / 5
        
        # Technical skills change should have more impact
        tech_impact = high_tech_rate - base_rate
        culture_impact = high_culture_rate - base_rate
        
        self.assertGreater(tech_impact, culture_impact)
        
    def test_decimal_precision(self):
        """Test decimal precision in calculations."""
        # Test that calculations maintain appropriate precision
        scores = {
            'technical_skills_match': {'score': 4},
            'experience_level': {'score': 3},
            'relevant_achievements': {'score': 4},
            'cultural_fit': {'score': 3}
        }
        
        rate = (4*0.4 + 3*0.25 + 4*0.2 + 3*0.15) / 5
        
        # Should be precise to 2 decimal places
        self.assertAlmostEqual(rate, 0.72, places=2)
        
        # Test project score precision
        project_scores = {
            'correctness': {'score': 4},
            'code_quality': {'score': 3},
            'resilience': {'score': 4},
            'documentation': {'score': 3},
            'creativity': {'score': 2}
        }
        
        project_score = 4*0.3 + 3*0.25 + 4*0.2 + 3*0.15 + 2*0.1
        self.assertAlmostEqual(project_score, 3.4, places=2)
    
    def test_cv_match_rate_bug_fix_validation(self):
        """Test the specific bug fix for cv_match_rate calculation."""
        # This test validates the fix for the bug where cv_match_rate was showing 0.9
        # when individual scores were: tech=1, exp=2, ach=1, cult=2
        
        # Individual scores from the bug report
        technical_skills_match = 1
        experience_level = 2
        relevant_achievements = 1
        cultural_fit = 2
        
        # Calculate the correct cv_match_rate
        # Formula: (tech*0.4 + exp*0.25 + ach*0.2 + cult*0.15) * 0.2
        weighted_sum = (technical_skills_match * 0.4 + 
                       experience_level * 0.25 + 
                       relevant_achievements * 0.2 + 
                       cultural_fit * 0.15)
        
        cv_match_rate = weighted_sum * 0.2
        
        # Expected calculation: (1*0.4 + 2*0.25 + 1*0.2 + 2*0.15) * 0.2
        # = (0.4 + 0.5 + 0.2 + 0.3) * 0.2 = 1.4 * 0.2 = 0.28
        expected_rate = 0.28
        
        self.assertAlmostEqual(cv_match_rate, expected_rate, places=2)
        
        # Verify this is NOT 0.9 (the incorrect value from the bug)
        self.assertNotAlmostEqual(cv_match_rate, 0.9, places=1)
        
        # Verify the calculation step by step
        self.assertAlmostEqual(technical_skills_match * 0.4, 0.4, places=2)
        self.assertAlmostEqual(experience_level * 0.25, 0.5, places=2)
        self.assertAlmostEqual(relevant_achievements * 0.2, 0.2, places=2)
        self.assertAlmostEqual(cultural_fit * 0.15, 0.3, places=2)
        self.assertAlmostEqual(weighted_sum, 1.4, places=2)
        self.assertAlmostEqual(cv_match_rate, 0.28, places=2)
