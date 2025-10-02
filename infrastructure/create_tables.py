import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def create_users_table():
    try:
        table = dynamodb.create_table(
            TableName='documentgpt-users',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        print("Users table created!")
    except Exception as e:
        if 'ResourceInUseException' in str(e):
            print("Users table exists")
        else:
            print(f"Error: {e}")

def create_cache_table():
    try:
        table = dynamodb.create_table(
            TableName='documentgpt-cache',
            KeySchema=[{'AttributeName': 'cache_key', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'cache_key', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        table.meta.client.update_time_to_live(
            TableName='documentgpt-cache',
            TimeToLiveSpecification={'AttributeName': 'ttl', 'Enabled': True}
        )
        print("Cache table created with TTL!")
    except Exception as e:
        if 'ResourceInUseException' in str(e):
            print("Cache table exists")
        else:
            print(f"Error: {e}")

if __name__ == "__main__":
    create_users_table()
    create_cache_table()
    print("Setup complete!")