import json
import boto3
from botocore.exceptions import ClientError
import requests
from requests_aws4auth import AWS4Auth
from collections import defaultdict



def lookup_dynamo_and_sort(cuisine, city, longitude, latitude):
    db = boto3.resource('dynamodb')
    table = db.Table(city)
    res = []
    # query by coordinates
    try:
        response = table.query(
            IndexName = 'rtype-rlongitude-index',
            KeyConditionExpression = (
                Key('cuisine').eq(cuisine) &
                Key('rlongitude').between(longitude-Decimal(0.003), longitude+Decimal(0.003))
                )
        )
    except ClientError as e:
        print('Error', e.response['Error']['Message'])
    else:
        for i in response['Items']:
            if latitude-Decimal(0.003) <= i['rlatitude'] <= latitude+Decimal(0.003):
                res.append(i)

        # start sorting
        all_res = defaultdict(lambda: {}) #structure: {'rid': {'info': ..., 'dist': ...}}
        for item in res:
            all_res[item['rid']]['info'] = item
            all_res[item['rid']]['dist'] = abs(all_res[item['rid']]['info']['rlatitude'] - latitude) \
            + abs(all_res[item['rid']]['info']['rlongitude'] - longitude)

        sorted_res = dict(sorted(all_res.items(), key=lambda item: (item[1]['info']['rrating'], item[1]['dist']), reverse = True))

    return sorted_res

def get_data(queue_url):
    sqs = boto3.client('sqs')

    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )

    message = response['Messages'][0]
    receipt_handle = message['ReceiptHandle']

    # Delete received message from queue
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )
    return message

def lambda_handler(event, context):
    # get from sqs
    message = get_data('https://sqs.us-east-1.amazonaws.com/415613607679/Restaurants')

    city = message['MessageAttributes']['City']['StringValue'].lower()
    longitude = Decimal(message['MessageAttributes']['Longitude']['StringValue'])
    latitude = Decimal(message['MessageAttributes']['Latitude']['StringValue'])
    cuisine = message['MessageAttributes']['Cuisine']['StringValue'].lower()
    email = message['MessageAttributes']['Email']['StringValue']

    # get from dynamo
    name = []
    address = []
    phone = []
    res = lookup_dynamo_and_sort(cuisine, city, longitude, latitude)
    count = 0
    for restaurant in res:
        count += 1
        if count > 3:
            break

        info = res[restaurant]['info']
        name.append(info['name'])
        address.append(info['address'])
        phone.append(info['phone'])

    #send email
    SENDER = "Dining Concierge Assistant <rz41314131@gmail.com>"
    RECIPIENT = email
    CONFIGURATION_SET = "ConfigSet"
    AWS_REGION = "us-east-1"
    SUBJECT = "YOUR PERSONALIZED RESTAURANT SUGGESTIONS"

    if len(name) == 3:
        BODY_HTML = """<html>
        <head></head>
        <body>
          <h1>YOUR PERSONALIZED RESTAURANT SUGGESTIONS</h1>
          <p>Hello! Here are my {} restaurant suggestions for you: 1. {}, located at {} and could be reached at {} 
          2. {}, located at {} and could be reached at {} 3. {}, located at {} and could be reached at {}.
          </p>
        </body>
        </html>
                """.format(cuisine,name[0],address[0],phone[0],name[1],address[1],phone[1],name[2],address[2],phone[2])
    elif len(name) == 2:
        BODY_HTML = """<html>
        <head></head>
        <body>
          <h1>YOUR PERSONALIZED RESTAURANT SUGGESTIONS</h1>
          <p>Hello! Here are my {} restaurant suggestions for you: 1. {}, located at {} and could be reached at {} 
          2. {}, located at {} and could be reached at {}.
          </p>
        </body>
        </html>
                """.format(cuisine,name[0],address[0],phone[0],name[1],address[1],phone[1])
    elif len(name) == 1:
        BODY_HTML = """<html>
        <head></head>
        <body>
          <h1>YOUR PERSONALIZED RESTAURANT SUGGESTIONS</h1>
          <p>Hello! Here are my {} restaurant suggestions for you: 1. {}, located at {} and could be reached at {}.
          </p>
        </body>
        </html>
                """.format(cuisine,name[0],address[0],phone[0])
    else:
        return

    CHARSET = "UTF-8"

    client = boto3.client('ses',region_name=AWS_REGION)
    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,

        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
    return
