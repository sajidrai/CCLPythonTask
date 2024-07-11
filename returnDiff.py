import json
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta
from decimal import Decimal
import logging

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('exchangeRates')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def query_exchange_rates(date):
    response = table.query(
        KeyConditionExpression=Key('Date').eq(date)
    )

    exchange_rates = response['Items'][0]['exchange_rates'] if response['Items'] else {}
    return exchange_rates

def lambda_handler(event, context):
    current_date = datetime.now().strftime("%Y-%m-%d")
    last_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    current_day_rates = query_exchange_rates(current_date)
    last_day_rates = query_exchange_rates(last_date)

    if not current_day_rates or not last_day_rates:
        error_message = ("Data not found for either the current day or the previous day. "
                         "or check if current day data is uploaded?")
        return {
            'statusCode': 404,
            'body': json.dumps({"error": error_message})
        }

    exchange_rate_differences = {}
    for currency, rate in current_day_rates.items():
        current_rate = float(rate)
        last_rate = float(last_day_rates.get(currency, 0))

        difference = current_rate - last_rate
        exchange_rate_differences[currency] = round(Decimal(str(difference)), 4)

    response = {
        "current_day_rates": {currency: str(rate) for currency, rate in current_day_rates.items()},
        "exchange_rate_differences": {currency: str(rate) for currency, rate in exchange_rate_differences.items()}
    }

    return {
        'statusCode': 200,
        'body': json.dumps(response)  
    }