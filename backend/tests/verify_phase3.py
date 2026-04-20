# verify_phase3.py — Verification script for MCQ Evaluation Pipeline.
# Tests OMR logic, TrOCR loading, and evaluator coordination.

import sys
import os
import numpy as np
import cv2
from PIL import Image
import unittest
from unittest.mock import MagicMock, patch

# Add app directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.omr_engine import OMREngine
from app.services.trocr_engine import TrOCREngine

class TestPhase3Implementation(unittest.TestCase):

    def setUp(self):
        self.omr = OMREngine(debug_dir="tests/debug_omr")
        self.trocr = TrOCREngine()

    def test_omr_logic_with_mock_image(self):
        """Generates a synthetic OMR sheet and verifies detection."""
        print("\n🔍 Testing OMR Engine...")
        
        # Create a black image
        height, width = 400, 300
        img = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # Draw some "bubbles" (circles)
        # We'll simulate 2 questions, each with A, B, C, D
        # Q1: A (filled), Q2: C (filled)
        choices_x = [50, 100, 150, 200]
        questions_y = [100, 200]
        
        for i, y in enumerate(questions_y):
            for j, x in enumerate(choices_x):
                # Draw bubble outline
                cv2.circle(img, (x, y), 15, (0, 0, 0), 2)
                
                # Fill bubbles for Q1:A and Q2:C
                if (i == 0 and j == 0) or (i == 1 and j == 2):
                    cv2.circle(img, (x, y), 12, (0, 0, 0), -1)

        test_img_path = "tests/mock_omr.png"
        cv2.imwrite(test_img_path, img)
        
        try:
            results = self.omr.process_image(test_img_path, mcq_count=2)
            print(f"✅ OMR Results: {results}")
            self.assertEqual(results.get("Q1"), "A")
            self.assertEqual(results.get("Q2"), "C")
        finally:
            if os.path.exists(test_img_path):
                os.remove(test_img_path)

    def test_trocr_parser(self):
        """Verifies the regex parsing of OCR text output."""
        print("🔍 Testing TrOCR Parser...")
        text = "Name: John Doe\n1. A\n2: B\n3 C\nRoll: 101"
        results = self.trocr.parse_mcq_results(text)
        print(f"✅ TrOCR Parse: {results}")
        self.assertEqual(results.get("Q1"), "A")
        self.assertEqual(results.get("Q2"), "B")
        self.assertEqual(results.get("Q3"), "C")

    @patch("os.path.exists")
    @patch("app.services.evaluator.papers_col")
    @patch("app.services.evaluator.submissions_col")
    @patch("app.services.evaluator.results_col")
    @patch("app.services.evaluator.log_evaluation_run")
    def test_evaluator_coordination(self, mock_log, mock_res, mock_sub, mock_paper, mock_exists):
        """Tests the evaluator logic flow with mocked dependencies."""
        print("🔍 Testing Evaluator Coordination...")
        from app.services.evaluator import evaluate_submission
        from bson import ObjectId
        from unittest.mock import AsyncMock

        # Mock File exists
        mock_exists.return_value = True

        # Mock Data
        sub_id = str(ObjectId())
        paper_id = str(ObjectId())
        
        # Setup AsyncMocks
        mock_sub.return_value.find_one = AsyncMock(return_value={
            "_id": ObjectId(sub_id),
            "paper_id": paper_id,
            "roll_no": "TEST001",
            "file_path": "tests/fake.png"
        })
        mock_sub.return_value.update_one = AsyncMock()
        
        mock_paper.return_value.find_one = AsyncMock(return_value={
            "_id": ObjectId(paper_id),
            "name": "Unit Test Paper",
            "type": "mcq",
            "mcqCount": 2,
            "mcqMarks": 2,
            "totalMarks": 4,
            "mcqAnswers": {"Q1": "A", "Q2": "B"},
            "prefers_omr": True
        })
        
        # insert_one needs to return an object with inserted_id
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = ObjectId()
        mock_res.return_value.insert_one = AsyncMock(return_value=mock_insert_result)

        # We need an async test runner for this
        import asyncio
        loop = asyncio.get_event_loop()
        
        # Override engines to avoid heavy loading
        with patch("app.services.evaluator._omr") as mock_omr_engine:
            mock_omr_engine.process_image.return_value = {"Q1": "A", "Q2": "B"}
            
            loop.run_until_complete(evaluate_submission(sub_id))
            
            # Verify database calls
            self.assertTrue(mock_res.return_value.insert_one.called)
            self.assertTrue(mock_sub.return_value.update_one.called)
            
            # Verify result score was 4 (2+2)
            result_doc = mock_res.return_value.insert_one.call_args[0][0]
            print(f"✅ Evaluator Score Calculated: {result_doc['score']}")
            self.assertEqual(result_doc["score"], 4.0)

if __name__ == "__main__":
    unittest.main()
