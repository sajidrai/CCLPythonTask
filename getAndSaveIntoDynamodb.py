import json
import boto3
import urllib.request
import logging
import xml.etree.ElementTree as ET
from decimal import Decimal

# Configuration
TABLE_NAME = 'exchangeRates'
HISTORICAL_XML_FILE_URL = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml'
DAILY_XML_FILE_URL = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
logger = logging.getLogger()
logger.setLevel(logging.INFO)
dynamodb = boto3.resource('dynamodb')
def download_xml_file(url):
    with urllib.request.urlopen(url) as response:
        if response.status != 200:
            raise Exception('Failed to download the XML file')
        return response.read()

def process_exchange_rates(xml_content, table):
    root = ET.fromstring(xml_content)
    insert_count = 0  # Counter to limit insertions to 5

    # Process and insert up to 5 entries
    for child in root:
        for c in child:
            if insert_count >= 5:
                break

            date = str(c.get('time'))
            exchange_rate_dict = {}
            for d in c:
                curr = d.get('currency')
                rate_str = d.get('rate')
                rate = Decimal(0)
                if rate_str and rate_str != 'NaN' and rate_str != 'NULL':
                    rate = Decimal(rate_str)
                exchange_rate_dict[curr] = rate

            if date and date != "None":
                # Update DynamoDB table with exchange rates
                table.put_item(Item={
                    'Date': date,
                    'exchange_rates': exchange_rate_dict
                })
                insert_count += 1


def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)
    return saveDataIntoDynamo(table)


def saveDataIntoDynamo(table):
    try:
        response = table.scan()
        items = response.get('Items', [])
        if len(items) == 0:
            logger.info("No entries found in DynamoDB. Downloading historical XML file.")
            xml_content = download_xml_file(HISTORICAL_XML_FILE_URL)
        else:
            logger.info("Data found in DynamoDB. Downloading daily XML file.")
            xml_content = download_xml_file(DAILY_XML_FILE_URL)

        # Process XML content
        process_exchange_rates(xml_content, table)

        return {'statusCode': 200, 'body': json.dumps('Data processed successfully')}

    except Exception as e:
        logger.error(f'An error occurred: {str(e)}')
        return {'statusCode': 500, 'body': json.dumps('An error occurred while processing the data')}