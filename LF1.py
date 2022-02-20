import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3
import json


def push_to_sqs(queue_url,City,Type,Num,Date,Time,Email):
    sqs = boto3.client('sqs')
    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=10,
        MessageAttributes={
            'City': {
                'DataType': 'String',
                'StringValue': City
            },
            'Cuisine': {
                'DataType': 'String',
                'StringValue': Type
            },
            'NumberOfAttendence': {
                'DataType': 'String',
                'StringValue': Num
            },
            'Date': {
                'DataType': 'String',
                'StringValue': Date
            },
            'Time': {
                'DataType': 'String',
                'StringValue': Time
            },
            'Email': {
                'DataType': 'String',
                'StringValue': Email
            }
        },
        MessageBody=(
            'Information about user preferred restaurant.'
        )
    )
    print(response['MessageId'])


def close(fulfillment_state, message):
    response = {
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
    return response


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }
    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def validate_Dining(City, Date, Type):
    Cities = ['manhattan']
    # Dates = ['today','tomorrow']
    Types = ['chinese','american','italian','japanese','indian','mexican']
    if City is not None and City.lower() not in Cities:
        return build_validation_result(False,
                                       'Manhattan',
                                       'We currently do not support {}, would you like to change to a different city?  '
                                       'Our most popular city is Manhattan'.format(City))

    if Type is not None and Type.lower() not in Types:
        return build_validation_result(False,
                                       'TypeOfCuisine',
                                       'We currently do not support {}, would you like to try something else?  '
                                       'You can choose among Chinese, Japanese, American, Indian, Italian, and Mexican.'
                                       'I personally suggest Chinese'.format(Type))
    return build_validation_result(True, None, None)


def Greeting(intent_request):
    source = intent_request['invocationSource']
    if source == 'DialogCodeHook':
        response = {
        "dialogAction":
            {"type": "Close",
             "fulfillmentState": "Fulfilled",
             "message": {
                 "contentType": "PlainText",
                 "content": 'Hi! What can I do for you?'
             }
             }
        };
        return response


def Thanks(intent_request):
    source = intent_request['invocationSource']
    if source == 'DialogCodeHook':
        response = {
        "dialogAction":
            {"type": "Close",
             "fulfillmentState": "Fulfilled",
             "message": {
                 "contentType": "PlainText",
                 "content": 'Bye!'
             }
             }
        };
        return response


def Dining(intent_request):
    City = intent_request['currentIntent']['slots']['Manhattan']
    Type = intent_request['currentIntent']['slots']['TypeOfCuisine']
    Num = intent_request['currentIntent']['slots']['NumberOfPeople']
    Date = intent_request['currentIntent']['slots']['Date']
    Time = intent_request['currentIntent']['slots']['Time']
    # Phone = intent_request['currentIntent']['slots']['PhoneNumber']
    Email = intent_request['currentIntent']['slots']['UserEmails']
    source = intent_request['invocationSource']
    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = intent_request['currentIntent']['slots']
        validation_result = validate_Dining(City, Date, Type)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        return delegate(output_session_attributes, intent_request['currentIntent']['slots'])

    push_to_sqs('https://sqs.us-east-1.amazonaws.com/415613607679/Restaurants',City,Type,Num,Date,Time,Email)
    response = {
        "dialogAction":
            {"type": "Close",
             "fulfillmentState": "Fulfilled",
             "message": {
                 "contentType": "PlainText",
                 "content": 'You’re all set. your reservation for {} Restaurant'
                 'in {} {} at {} with attendence of {} people has been placed! '
                 'Your Email Address is {}. Expect my suggestions shortly! '
                 'Have a good day.'.format(Type,City,Date,Time,Num,Email)
             }
             }
    };
    return response


def dispatch(intent_request):
    intent_name = intent_request['currentIntent']['name']
    if intent_name == 'DiningConciergeAssistant':
        return Dining(intent_request)
    if intent_name == 'GreetingIntent':
        return Greeting(intent_request)
    if intent_name == 'ThanksIntent':
        return Thanks(intent_request)
    raise Exception('Intent with name ' + intent_name + ' not supported')


def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    return dispatch(event)
