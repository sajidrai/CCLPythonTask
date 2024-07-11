import json
import unittest
from datetime import datetime, timedelta
from returnDiff import lambda_handler, query_exchange_rates
from unittest.mock import patch

class TestLambdaHandler(unittest.TestCase):

    def test_query_exchange_rates(self):
        with patch('returnDiff.query_exchange_rates') as mock_query_exchange_rates:
            # Mock exchange rate data
            mock_query_exchange_rates.return_value = {'USD': '1.2', 'EUR': '0.9'}

            # Call the lambda_handler function with event and context arguments
            result = lambda_handler({}, {})

            # Assert the response
            expected_response = {
            "current_day_rates": {'USD': '1.2', 'EUR': '0.9'},
            "exchange_rate_differences": {'USD': '0.0000', 'EUR': '0.0000'}
            }
            self.assertDictEqual(json.loads(result['body']), expected_response)

    @patch('returnDiff.query_exchange_rates')
    def test_lambda_handler(self, query_mock):
        # Mocking the exchange rate data for the current and last day
        current_day_rates = {'USD': '1.2', 'EUR': '0.9'}
        last_day_rates = {'USD': '1.0', 'EUR': '0.8'}

        current_date = datetime.now().strftime("%Y-%m-%d")
        last_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        query_mock.side_effect = lambda date: current_day_rates if date == current_date else last_day_rates

        # Calling the lambda handler function
        result = lambda_handler(None, None)

        # Validating the results
        expected_response = {
        "current_day_rates": {'USD': '1.2', 'EUR': '0.9'},
        "exchange_rate_differences": {'USD': '0.2000', 'EUR': '0.1000'}
        }
        expected_status_code = 200

        self.assertEqual(result['statusCode'], expected_status_code)
        self.assertDictEqual(json.loads(result['body']), expected_response)

if __name__ == '__main__':
    unittest.main()