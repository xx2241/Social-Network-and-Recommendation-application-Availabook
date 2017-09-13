# This is a simple connection to DynamoDB with get/put/update/delete function
# Please fill in the Aceess_key and Secret_access_key first
# Please create a table named "User" with the following columns:
# id | first_name | last_name

from boto3.session import Session

dynamodb_session = Session(aws_access_key_id="ACCESS_KEY",
              aws_secret_access_key="SECRET_ACCESS_KEY",
              region_name="us-east-1")
dynamodb = dynamodb_session.resource('dynamodb')

table = dynamodb.Table("User")

# get function
def get():
    response = table.get_item(
        Key={
            'id': 1
        }
    )
    item = response['Item']
    print(item)

# put function
def put(id, first_name, last_name):
    table.put_item(
        Item={
            'id': id,
            'first_name': first_name,
            'last_name': last_name
        }
    )

# update function
def update(id, first_name, last_name):
    table.update_item(
        Key={
            'id': id
        },
        UpdateExpression='SET first_name = :val1, last_name = :val2',
        ExpressionAttributeValues={
            ':val1': first_name,
            ':val2': last_name
        }
    )

# delete function
def delete(id):
    table.delete_item(
        Key={
            'id': id
        }
    )

if __name__ == '__main__':
    delete()
