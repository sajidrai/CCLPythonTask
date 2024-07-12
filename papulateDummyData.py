import boto3
from datetime import datetime, timedelta

# Initialize DynamoDB resource using the default session
dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')

# Specify the DynamoDB table
table = dynamodb.Table('exchangeRates')

def copy_data_from_two_days_ago():
    # Get the current date and the date two days ago
    current_date = datetime.utcnow().strftime('%Y-%m-%d')
    two_days_ago = (datetime.utcnow() - timedelta(days=2)).strftime('%Y-%m-%d')

    # Retrieve the data from two days ago
    response = table.get_item(Key={'Date': two_days_ago})

    if 'Item' in response:
        two_days_ago_data = response['Item']['exchange_rates']

        # Insert the data with the current date
        table.put_item(Item={
            'Date': current_date,
            'exchange_rates': two_days_ago_data
        })
        print(f"Inserted data for current date {current_date} from {two_days_ago}")
    else:
        print(f"No data found for {two_days_ago}")

if __name__ == "__main__":
    copy_data_from_two_days_ago()