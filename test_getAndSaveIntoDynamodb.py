import unittest
from unittest.mock import MagicMock, patch
import getAndSaveIntoDynamodb  # Use absolute import
from getAndSaveIntoDynamodb import lambda_handler
from decimal import Decimal


class TestLambdaHandler(unittest.TestCase):

    HISTORICAL_XML_FILE_LINK = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"
    DAILY_XML_FILE_LINK = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
    XML_DATA = """<?xml version="1.0" encoding="UTF-8"?>
                    <gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01" xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
                        <gesmes:subject>Reference rates</gesmes:subject>
                        <gesmes:Sender>
                            <gesmes:name>European Central Bank</gesmes:name>
                        </gesmes:Sender>
                        <Cube>
                            <Cube time="2024-07-09">
                                <Cube currency="USD" rate="1.0814"/>
                                <Cube currency="JPY" rate="174.2"/>
                                <!-- Add more Cube elements as needed -->
                            </Cube>
                        </Cube>
                    </gesmes:Envelope>
                    """

    @patch('getAndSaveIntoDynamodb.process_exchange_rates')
    @patch('getAndSaveIntoDynamodb.download_xml_file')
    @patch('getAndSaveIntoDynamodb.boto3.resource')
    def test_lambda_handler_process_exchange_rates_called_with_daily_data(self, mock_boto3_resource, mock_download_xml_file,
                                                                                mock_process_exchange_rates
                                                                               ):
        # Mock DynamoDB resource and table
        mock_table = MagicMock()
        mock_table.query.return_value = {'Count': 1}
        mock_table.scan.return_value = {'Items': [{'example_item': 'value'}]}
        mock_boto3_resource().Table.return_value = mock_table

        # Mock download_xml_file to return test XML data
        mock_download_xml_file.return_value = self.XML_DATA

        # Call lambda_handler
        # getAndSaveIntoDynamodb.lambda_handler({}, None)
        getAndSaveIntoDynamodb.saveDataIntoDynamo(mock_table)

        # Assert that download_xml_file was called with the correct URL
        mock_download_xml_file.assert_called_once_with(self.DAILY_XML_FILE_LINK)

        # Assert that process_exchange_rates was called with the XML data and the mock table
        mock_process_exchange_rates.assert_called_once_with(self.XML_DATA, mock_table)

    @patch('getAndSaveIntoDynamodb.boto3.resource')
    @patch('getAndSaveIntoDynamodb.boto3.client')
    @patch('getAndSaveIntoDynamodb.download_xml_file')
    @patch('getAndSaveIntoDynamodb.process_exchange_rates')
    def test_lambda_handler_process_exchange_rates_called_with_historical_data(self, mock_process_exchange_rates,
                                                                               mock_download_xml_file,
                                                                               mock_boto3_client,
                                                                               mock_boto3_resource):
        # Mock DynamoDB resource and table
        mock_table = MagicMock()
        mock_boto3_resource.return_value.Table.return_value = mock_table
        mock_table.query.return_value = {'Count': 0}

        # Mock DynamoDB client for any client-based operations (if applicable)
        mock_dynamodb_client = MagicMock()
        mock_boto3_client.return_value = mock_dynamodb_client

        # Mock download_xml_file to return test XML data
        mock_download_xml_file.return_value = self.XML_DATA

        # Call lambda_handler
        getAndSaveIntoDynamodb.saveDataIntoDynamo(mock_table)

        # Assert that download_xml_file was called with the correct URL
        mock_download_xml_file.assert_called_once_with(self.HISTORICAL_XML_FILE_LINK)

        # Assert that process_exchange_rates was called with the XML data and the mock table
        mock_process_exchange_rates.assert_called_once_with(self.XML_DATA, mock_table)

    @patch('getAndSaveIntoDynamodb.boto3.resource')
    def test_process_exchange_rates(self, mock_resource):
        table = MagicMock()
        mock_resource().Table.return_value = table

        # Call the process_exchange_rates function
        getAndSaveIntoDynamodb.process_exchange_rates(TestLambdaHandler.XML_DATA,table)

        # Additional debugging
        print(f"put_item call count: {table.put_item.call_count}")
        print(f"put_item call args: {table.put_item.call_args_list}")

        # Assert that table.put_item was called with the correct arguments
        table.put_item.assert_called_once_with(Item={
            'Date': '2024-07-09',
            'exchange_rates': {
                'USD': Decimal('1.0814'),
                'JPY': Decimal('174.2')
            }
        })

if __name__ == '__main__':
    unittest.main()
