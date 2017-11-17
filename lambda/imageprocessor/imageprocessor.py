# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Amazon Software License (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at
#     http://aws.amazon.com/asl/
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and limitations under the License.

from __future__ import print_function
import base64
import datetime
import time
import decimal
import uuid
import json
import cPickle
import boto3
import pytz
from pytz import timezone
from copy import deepcopy


def load_config():
    '''Load configuration from file.'''
    with open('imageprocessor-params.json', 'r') as conf_file:
        conf_json = conf_file.read()
        return json.loads(conf_json)

def convert_ts(ts, config):
    '''Converts a timestamp to the configured timezone. Returns a localized datetime object.'''
    #lambda_tz = timezone('US/Pacific')
    tz = timezone(config['timezone'])
    utc = pytz.utc

    utc_dt = utc.localize(datetime.datetime.utcfromtimestamp(ts))

    localized_dt = utc_dt.astimezone(tz)

    return localized_dt

def process_image(event, context):

    #Initialize clients
    rekog_client = boto3.client('rekognition')
    sns_client = boto3.client('sns')
    s3_client = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')

    #Load config
    config = load_config()

    s3_bucket = config["s3_bucket"]
    s3_key_frames_root = config["s3_key_frames_root"]

    ddb_table = dynamodb.Table(config["ddb_table"])

    #Iterate on frames fetched from Kinesis
    for record in event['Records']:

        frame_package_b64 = record['kinesis']['data']
        frame_package = cPickle.loads(base64.b64decode(frame_package_b64))

        img_bytes = frame_package["ImageBytes"]
        approx_capture_ts = frame_package["ApproximateCaptureTime"]
        frame_count = frame_package["FrameCount"]

        now_ts = time.time()

        frame_id = str(uuid.uuid4())
        processed_timestamp = decimal.Decimal(now_ts)
        approx_capture_timestamp = decimal.Decimal(approx_capture_ts)

        now = convert_ts(now_ts, config)
        year = now.strftime("%Y")
        mon = now.strftime("%m")
        day = now.strftime("%d")
        hour = now.strftime("%H")

        face_details = rekog_client.detect_faces(
            Image={
                'Bytes': img_bytes
            },
            Attributes=['ALL']
        )

        #Iterate on rekognition labels. Enrich and prep them for storage in DynamoDB
        item_proc = face_details
        for faceDetail in face_details['FaceDetails']:

            ageLow = faceDetail['AgeRange']['Low']
            ageHigh = faceDetail['AgeRange']['High']
            faceDetail['OnWatchList'] = False

            prime_emotion = "Unknown"
            high_emotion = 0
            num_emotion = 0
            num_landmarks = 0
            anger_track = 0
            for emotion in faceDetail['Emotions']:
                num_emotion += 1
                conf = emotion['Confidence']
                emotion['Confidence'] = str(conf) # Float to Decimal for DynamoDB
                if high_emotion <= conf:
                    high_emotion = conf
                    prime_emotion = emotion['Type']
                    if prime_emotion == "ANGRY" or prime_emotion == "DISGUSTED":
                        anger_track = num_emotion
            for landmarks in faceDetail['Landmarks']:
                num_landmarks += 1

            #Print labels to lambda console
            print('Age {} to {}. Prime Emotion: {}'.format(ageLow, ageHigh, prime_emotion))

            #Check faceDetail watch list and trigger action
            # if (prime_emotion == "ANGRY" or prime_emotion == "DISGUSTED" and high_emotion >= label_watch_min_conf):
            #     faceDetail['OnWatchList'] = True
            #     labels_on_watch_list.append(deepcopy(faceDetail))

            #Convert from float to decimal for DynamoDB
            i = 0
            while(i < num_emotion):
                faceDetail['Emotions'][i]['Confidence'] = decimal.Decimal(str(faceDetail['Emotions'][i]['Confidence']))
                i += 1
            i = 0
            faceDetail['Confidence'] = decimal.Decimal(str(faceDetail['Confidence']))
            faceDetail['AgeRange']['High'] = decimal.Decimal(str(faceDetail['AgeRange']['High']))
            faceDetail['AgeRange']['Low'] = decimal.Decimal(str(faceDetail['AgeRange']['Low']))
            faceDetail['BoundingBox']['Height'] = decimal.Decimal(str(faceDetail['BoundingBox']['Height']))
            faceDetail['BoundingBox']['Left'] = decimal.Decimal(str(faceDetail['BoundingBox']['Left']))
            faceDetail['BoundingBox']['Top'] = decimal.Decimal(str(faceDetail['BoundingBox']['Top']))
            faceDetail['BoundingBox']['Width'] = decimal.Decimal(str(faceDetail['BoundingBox']['Width']))

            while(i < num_landmarks):
                faceDetail['Landmarks'][i]['X'] = decimal.Decimal(str(faceDetail['Landmarks'][i]['X']))
                faceDetail['Landmarks'][i]['Y'] = decimal.Decimal(str(faceDetail['Landmarks'][i]['Y']))
                i += 1

            faceDetail['Pose']['Pitch'] = decimal.Decimal(str(faceDetail['Pose']['Pitch']))
            faceDetail['Pose']['Roll'] = decimal.Decimal(str(faceDetail['Pose']['Roll']))
            faceDetail['Pose']['Yaw'] = decimal.Decimal(str(faceDetail['Pose']['Yaw']))
            faceDetail['Quality']['Brightness'] = decimal.Decimal(str(faceDetail['Quality']['Brightness']))
            faceDetail['Quality']['Sharpness'] = decimal.Decimal(str(faceDetail['Quality']['Sharpness']))
            faceDetail['Beard']['Confidence'] = decimal.Decimal(str(faceDetail['Beard']['Confidence']))
            faceDetail['Eyeglasses']['Confidence'] = decimal.Decimal(str(faceDetail['Eyeglasses']['Confidence']))
            faceDetail['EyesOpen']['Confidence'] = decimal.Decimal(str(faceDetail['EyesOpen']['Confidence']))
            faceDetail['Gender']['Confidence'] = decimal.Decimal(str(faceDetail['Gender']['Confidence']))
            faceDetail['MouthOpen']['Confidence'] = decimal.Decimal(str(faceDetail['MouthOpen']['Confidence']))
            faceDetail['Mustache']['Confidence'] = decimal.Decimal(str(faceDetail['Mustache']['Confidence']))
            faceDetail['Smile']['Confidence'] = decimal.Decimal(str(faceDetail['Smile']['Confidence']))
            faceDetail['Sunglasses']['Confidence'] = decimal.Decimal(str(faceDetail['Sunglasses']['Confidence']))
            item_proc = faceDetail

        #Store frame image in S3
        s3_key = (s3_key_frames_root + '{}/{}/{}/{}/{}.jpg').format(year, mon, day, hour, frame_id)

        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=img_bytes
        )

        #Persist frame data in dynamodb

        item = {
            'frame_id': frame_id,
            'processed_timestamp' : processed_timestamp,
            'approx_capture_timestamp' : approx_capture_timestamp,
            'AgeRangeLow' : item_proc['AgeRange']['Low'],
            'AgeRangeHigh' : item_proc['AgeRange']['High'],
            'BeardConfidence' : decimal.Decimal(str(item_proc['Beard']['Confidence'])),
            'BeardValue' : item_proc['Beard']['Value'],
            'BoundingBoxHeight' : decimal.Decimal(str(item_proc['BoundingBox']['Height'])),
            'BoundingBoxLeft' : decimal.Decimal(str(item_proc['BoundingBox']['Left'])),
            'BoundingBoxTop' : decimal.Decimal(str(item_proc['BoundingBox']['Top'])),
            'BoundingBoxWidth' : decimal.Decimal(str(item_proc['BoundingBox']['Width'])),
            'FaceConfidence' : decimal.Decimal(str(item_proc['Confidence'])),
            'Emotion' : prime_emotion,
            'EmotionConfidence' : decimal.Decimal(str(high_emotion)),
            'EyeglassesConfidence' : decimal.Decimal(str(item_proc['Eyeglasses']['Confidence'])),
            'EyeglassesValue' : item_proc['Eyeglasses']['Value'],
            'EyesOpenConfidence' : decimal.Decimal(str(item_proc['EyesOpen']['Confidence'])),
            'EyesOpenValue' : item_proc['EyesOpen']['Value'],
            'GenderConfidence' : decimal.Decimal(str(item_proc['Gender']['Confidence'])),
            'GenderValue' : item_proc['Gender']['Value'],
            'MouthOpenConfidence' : decimal.Decimal(str(item_proc['MouthOpen']['Confidence'])),
            'MouthOpenValue' : item_proc['MouthOpen']['Value'],
            'MustacheConfidence' : decimal.Decimal(str(item_proc['Mustache']['Confidence'])),
            'MustacheValue' : item_proc['Mustache']['Value'],
            'EyesOpenConfidence' : decimal.Decimal(str(item_proc['EyesOpen']['Confidence'])),
            'EyesOpenValue' : item_proc['EyesOpen']['Value'],
            'PosePitch' : decimal.Decimal(str(item_proc['Pose']['Pitch'])),
            'PoseRoll' : decimal.Decimal(str(item_proc['Pose']['Roll'])),
            'PoseYaw' : decimal.Decimal(str(item_proc['Pose']['Yaw'])),
            'QualityBrightness' : decimal.Decimal(str(item_proc['Quality']['Brightness'])),
            'QualitySharpness' : decimal.Decimal(str(item_proc['Quality']['Sharpness'])),
            'SmileConfidence' : decimal.Decimal(str(item_proc['Smile']['Confidence'])),
            'SmileValue' : item_proc['Smile']['Value'],
            'SunglassesConfidence' : decimal.Decimal(str(item_proc['Sunglasses']['Confidence'])),
            'SunglassesValue' : item_proc['Sunglasses']['Value'],
            'processed_year_month' : year + mon, #To be used as a Hash Key for DynamoDB GSI
            's3_bucket' : s3_bucket,
            's3_key' : s3_key
        }

        ddb_table.put_item(Item=item)

    print('Successfully processed {} records.'.format(len(event['Records'])))
    return

def handler(event, context):
    return process_image(event, context)
