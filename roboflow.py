import requests
import sys
import cv2
import base64
import io
import json
import urllib.parse
import random
import numpy as np
import os.path
from PIL import Image
from requests.adapters import HTTPAdapter, Retry

SEGMENTATION_THRESHOLD = 0.1
SEGMENTATION_PADDING = 60

CLASSIFICATION_PADDING = 30

COLORS = {
'Reflux esophagitis -La-A-': tuple(random.randint(0,255) for x in range(3)),
'Corpus gastricum': tuple(random.randint(0,255) for x in range(3)),
'Polyp -type Is-': tuple(random.randint(0,255) for x in range(3)),
'Atrophic superficial gastritis': tuple(random.randint(0,255) for x in range(3)),
'Mouth': tuple(random.randint(0,255) for x in range(3)),
'Antrum pyloricum': tuple(random.randint(0,255) for x in range(3)),
'Esophagus': tuple(random.randint(0,255) for x in range(3)),
'Duodenum': tuple(random.randint(0,255) for x in range(3))
}

VIDEO_NAME = sys.argv[1]
TYPES = {
    "SEGMENTATION": {
        "KEY": "dKmUZU6MLwX9R504E4M1",
        "PREFIX": "https://outline.roboflow.com/instance-d8qr5/1"
    },
    "CLASSIFICATION": {
        "KEY": "YQYAOWDsYtkXsusKdvxd",
        "PREFIX": "https://classify.roboflow.com/endo-navi-gastro-v-1.0/1"
    }
}
SCORES = []

session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[104, 500, 502, 503, 504] )
session.mount('https://', HTTPAdapter(max_retries=retries))

def getPrediction(fname, jpg_as_text, img_name, prediction_type):
    try:
        with open(fname) as f:
            data = json.loads(f.read())
    except:
        segmentation_url = "{}?api_key={}&name={}.jpg".format(
            TYPES[prediction_type]["PREFIX"],
            TYPES[prediction_type]["KEY"],
            img_name)
        r = session.post(segmentation_url, data=jpg_as_text, headers={
            "Content-Type": "application/x-www-form-urlencoded"
        })
        data = r.json()
    with open(fname,'w') as f:
        f.write(json.dumps(data,indent=4))
    return data


def drawSegmentation(frame, jpg_as_text, count, img_name):
    fname = 'predictions/{}_prediction_segmentation4_{}.json'.format(VIDEO_NAME, count)
    data = getPrediction(fname, jpg_as_text, img_name, "SEGMENTATION")
    vertical = SEGMENTATION_PADDING
    detected = False
    for obj in data["predictions"]:
        confidence = obj['confidence']
        if confidence < SEGMENTATION_THRESHOLD:
            continue
        text = obj['class'] + ': ' + str(confidence)
        color = COLORS[obj['class']]
        center = tuple((10,vertical))
        vertical += 30
        points = []
        if len(obj["points"]) > 0:
            for point in obj["points"]:
                points.append([point["x"], point["y"]])
            pts = np.array(points, np.int32)
            pts = pts.reshape((-1, 1, 2))
            isClosed = True
            thickness = 2
            frame = cv2.polylines(frame, [pts],
                                    isClosed, color, thickness)
            frame = cv2.putText(frame, text, center,
                                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    return frame

def drawClassification(frame, jpg_as_text, count, img_name):
    fname = 'predictions/{}_prediction_classification_{}.json'.format(VIDEO_NAME, count)
    data = getPrediction(fname, jpg_as_text, img_name, "CLASSIFICATION")
    score = {k: v['confidence'] for k, v in data['predictions'].items()}
    predictions =  {k: 0 for k, v in data['predictions'].items()}
    SCORES.insert(0, score)
    if len(SCORES) > 20:
        SCORES.pop(-1)
    i = 0
    for s in SCORES:
        for prediction, v in s.items():
            predictions[prediction] += v / sum(s.values())
        i += 1
    prediction_score = {k: v for k, v in sorted(predictions.items(), key=lambda item: -item[1])}
    pred_i = 0
    for k, v in prediction_score.items():
        if k == 'Oropharynx': k = 'Oesophagus'
        elif k == 'Oesophagus': k = 'Oropharynx'
        break
    text = "{}: {}".format(k, round(v,3))
    frame = cv2.putText(frame, text, (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    return frame


def getFrames():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1)
    session.mount('http://', HTTPAdapter(max_retries=retries))

    video_in = cv2.VideoCapture(VIDEO_NAME)
    ok, frame = video_in.read()
    height,width,layers = frame.shape
    fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    video_out=cv2.VideoWriter('detections_' + VIDEO_NAME, fourcc, 20.0, (width,height))
    count = 0
    scores = []
    switches = 0
    pred = None
    while ok:
        img_name = "frame" + str(count)
        retval, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer)
        frame = drawSegmentation(frame, jpg_as_text, count, img_name)
        frame = drawClassification(frame, jpg_as_text, count, img_name)
        count+=1
        if count % 10 == 0:
            print(count)
        #cv2.imwrite("image.jpg",frame)
        video_out.write(frame)
        ok, frame = video_in.read()
    
    cv2.destroyAllWindows()
    video_in.release()
    video_out.release()

getFrames()
