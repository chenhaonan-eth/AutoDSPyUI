import unittest
from unittest.mock import patch, MagicMock
from dspyui.core.mlflow_service import register_compiled_model, validate_model_name, ModelRegistrationResult

class TestMLflowService(unittest.TestCase):
    
    def test_validate_model_name_empty(self):
        is_valid, error_code = validate_model_name("")
        self.assertFalse(is_valid)
        self.assertEqual(error_code, "empty_name")
        
        is_valid, error_code = validate_model_name("   ")
        self.assertFalse(is_valid)
        self.assertEqual(error_code, "empty_name")

    def test_validate_model_name_valid(self):
        is_valid, error_code = validate_model_name("valid-model")
        self.assertTrue(is_valid)
        self.assertIsNone(error_code)

    @patch('dspyui.core.mlflow_service.MLFLOW_ENABLED', False)
    def test_register_disabled_mlflow(self):
        result = register_compiled_model("run_id", "name", {})
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "mlflow_disabled")

    @patch('dspyui.core.mlflow_service.MLFLOW_ENABLED', True)
    def test_register_no_run_id(self):
        result = register_compiled_model(None, "name", {})
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "no_run_id")

    @patch('dspyui.core.mlflow_service.MLFLOW_ENABLED', True)
    @patch('dspyui.core.mlflow_service.register_model')
    @patch('dspyui.core.mlflow_service.get_mlflow_ui_url')
    def test_register_success(self, mock_url, mock_register):
        mock_register.return_value = "1"
        mock_url.return_value = "http://mlflow/model/1"
        
        prompt_details = {
            "input_fields": ["a"],
            "output_fields": ["b"],
            "instructions": "do it",
            "evaluation_score": 0.9
        }
        
        result = register_compiled_model("run-123", "test-model", prompt_details)
        
        self.assertTrue(result.success)
        self.assertEqual(result.version, "1")
        self.assertEqual(result.model_url, "http://mlflow/model/1")
        mock_register.assert_called_once()

    @patch('dspyui.core.mlflow_service.MLFLOW_ENABLED', True)
    @patch('dspyui.core.mlflow_service.register_model')
    def test_register_failure_api(self, mock_register):
        mock_register.return_value = None
        
        result = register_compiled_model("run-123", "test-model", {})
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "registration_failed")

    @patch('dspyui.core.mlflow_service.MLFLOW_ENABLED', True)
    @patch('dspyui.core.mlflow_service.register_model')
    def test_register_exception(self, mock_register):
        mock_register.side_effect = Exception("MLflow error")
        
        result = register_compiled_model("run-123", "test-model", {})
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "exception")
        self.assertIn("MLflow error", result.error_message)

if __name__ == '__main__':
    unittest.main()
