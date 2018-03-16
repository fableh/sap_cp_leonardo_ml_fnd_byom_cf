import os
from grpc.beta import implementations
import tensorflow as tf
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2

import json
import requests
import flask
from flask import Flask, globals, request, g

app = Flask(__name__)


MODEL_NAME = str(os.getenv('MODEL_NAME', ''))
MODEL_SERVER_HOST = str(os.getenv('MODEL_SERVER_HOST', ''))
MODEL_SERVER_PORT = int(os.getenv('MODEL_SERVER_PORT', ''))

ROOT_CERT = str(os.getenv('ROOT_CERT', '')).replace('\\n', '\n')

def get_access_token():
 	url = 'https://sycor-cf-subaccount.authentication.eu10.hana.ondemand.com/oauth/token?'
 	querystring = {'grant_type': 'client_credentials'}
 	headers = {
 	'authorization': 'Basic c2ItNDc2MDFjMjctOTI2OC00MGQxLTk2ZDgtOGU5MmRhYWE3NDAxIWIxMTY1fG1sLWZvdW5kYXRpb24teHN1YWEtc3RkIWI1NDA6NC9kK0R4L0NjY0F6SGZYbkVwcFdwSDZLY09nPQ==',
 	'content-type': 'application/x-www-form-urlencoded'
 	}
 	response = requests.request('POST', url, headers=headers, params=querystring)
 	return 'Bearer ' + json.loads(response.text)['access_token']

def metadata_transformer(metadata):
    additions = []
    token = get_access_token()
    additions.append(('authorization', token))
    return tuple(metadata) + tuple(additions)

@app.route('/', methods=['POST'])

def main():
    credentials = implementations.ssl_channel_credentials(root_certificates=ROOT_CERT)
    channel = implementations.secure_channel(MODEL_SERVER_HOST, MODEL_SERVER_PORT, credentials)
    stub = prediction_service_pb2.beta_create_PredictionService_stub(channel, metadata_transformer=metadata_transformer)

    # process the first file only
    uploaded_files = globals.request.files.getlist('file')
    data = uploaded_files[0].read()

    # See prediction_service.proto for gRPC request/response details. 
    # change input type and data shapes according to your model
    request = predict_pb2.PredictRequest()
    request.model_spec.name = MODEL_NAME
    request.model_spec.signature_name = 'predict_images'
    request.inputs['images'].CopyFrom(
        tf.contrib.util.make_tensor_proto(data, shape=[1]))

    return str(stub.Predict(request, 120))

port = os.getenv('PORT', '5000')
if __name__ == '__main__':
    app.debug = not os.getenv('PORT')
    app.run(host='0.0.0.0', port=int(port))