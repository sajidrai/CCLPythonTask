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
    print(f"Processing {xml_content}")
    root = ET.fromstring(xml_content)
    insert_count = 0  # Counter to limit insertions to 5
    print(f"in process_exchange_rates")
    for child in root:
        for c in child:
            if insert_count >= 5:
                break

            date = str(c.get('time'))
            exchange_rate_dict = {}
            logger.info(f"date: {date}")
            for d in c:
                curr = d.get('currency')
                rate_str = d.get('rate')
                rate = Decimal(0)
                if rate_str and rate_str != 'NaN' and rate_str != 'NULL':
                    rate = Decimal(rate_str)
                else:
                    rate = Decimal(0)
                exchange_rate_dict[curr] = rate
            print(f"befor in put_item")
            print(f"date: {date}")
            print(f"table: {table}")
            if date != "None":
                print(f"date in if: {date}")
                print(f"exchange_rate_dict: {exchange_rate_dict}")
                # Update DynamoDB table with exchange rates
                table.put_item(Item={
                    'Date': date,
                    'exchange_rates': exchange_rate_dict
                })
                print(f"after put_item")
                insert_count += 1


def lambda_handler(event, context):
    print(f"in lambda_handler")
    table = dynamodb.Table(TABLE_NAME)
    return saveDataIntoDynamo(table)


def saveDataIntoDynamo(table):
    try:
        response = table.scan()
        items = response.get('Items', [])
        print(f"item count: {len(items)}")
        if len(items) == 0:
            print(f"item count 0")
            logger.info("No entries found in DynamoDB. Downloading historical XML file.")
            xml_content = download_xml_file(HISTORICAL_XML_FILE_URL)
        else:
            print(f"item count not zero: {len(items)}")
            logger.info("Data found in DynamoDB. Downloading daily XML file.")
            xml_content = download_xml_file(DAILY_XML_FILE_URL)

        # Process XML content
        print(f"before process_exchange_rates")
        process_exchange_rates(xml_content, table)
        print(f"after process_exchange_rates")

        return {'statusCode': 200, 'body': json.dumps('Data processed successfully')}

    except Exception as e:
        logger.error(f'An error occurred: {str(e)}')
        return {'statusCode': 500, 'body': json.dumps('An error occurred while processing the data')}