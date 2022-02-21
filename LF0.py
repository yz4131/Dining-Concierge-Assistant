import boto3
import json


client = boto3.client('lex-runtime')
def lambda_handler(event, context):
    msg_from_user = event['messages'][0]['unstructured']['text']

    response = client.post_text(botName='chatbot',
                                botAlias='Chatbot',
                                userId='testuser',
                                inputText=msg_from_user)

    msg_from_lex = response['message']
    if msg_from_lex:

        resp = {
            'statusCode':200,
            'messages': [
                {
                    "type":"unstructured",
                    "unstructured":{
                        "text":msg_from_lex
                    }
                }
                ]
        }
    print(resp)

    return resp
