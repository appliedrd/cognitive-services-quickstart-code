# <snippet_imports>
import asyncio
import io
import glob
import os
import sys
import time
import uuid
import requests
from urllib.parse import urlparse
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
import textwrap
from azure.cognitiveservices.vision.face.models import TrainingStatusType, Person, SnapshotObjectType, \
    OperationStatusType, Emotion, FaceAttributeType

# </snippet_imports>

'''
Face Quickstart

Examples include:
    - Detect Faces: detects faces in an image.
    - Find Similar: finds a similar face in an image using ID from Detect Faces.
    - Verify: compares two images to check if they are the same person or not.
    - Person Group: creates a person group and uses it to identify faces in other images.
    - Large Person Group: similar to person group, but with different API calls to handle scale.
    - Face List: creates a list of single-faced images, then gets data from list.
    - Large Face List: creates a large list for single-faced images, trains it, then gets data.
    - Snapshot: copies a person group from one region to another, or from one Azure subscription to another.

Prerequisites:
    - Python 3+
    - Install Face SDK: pip install azure-cognitiveservices-vision-face
    - In your root folder, add all images downloaded from here:
      https://github.com/Azure-examples/cognitive-services-sample-data-files/tree/master/Face/images
How to run:
    - Run from command line or an IDE
    - If the Person Group or Large Person Group (or Face List / Large Face List) examples get
      interrupted after creation, be sure to delete your created person group (lists) from the API,
      as you cannot create a new one with the same name. Use 'Person group - List' to check them all,
      and 'Person Group - Delete' to remove one. The examples have a delete function in them, but at the end.
      Person Group API: https://westus.dev.cognitive.microsoft.com/docs/services/563879b61984550e40cbbe8d/operations/563879b61984550f30395244
      Face List API: https://westus.dev.cognitive.microsoft.com/docs/services/563879b61984550e40cbbe8d/operations/563879b61984550f3039524d
References:
    - Documentation: https://docs.microsoft.com/en-us/azure/cognitive-services/face/
    - SDK: https://docs.microsoft.com/en-us/python/api/azure-cognitiveservices-vision-face/azure.cognitiveservices.vision.face?view=azure-python
    - All Face APIs: https://docs.microsoft.com/en-us/azure/cognitive-services/face/APIReference
'''

# <snippet_subvars>
# Set the FACE_SUBSCRIPTION_KEY environment variable with your key as the value.
# This key will serve all examples in this document.
KEY = os.environ['FACE_SUBSCRIPTION_KEY']

# Set the FACE_ENDPOINT environment variable with the endpoint from your Face service in Azure.
# This endpoint will be used in all examples in this quickstart.
ENDPOINT = os.environ['FACE_ENDPOINT']
# </snippet_subvars>

# <snippet_verify_baseurl>
# Base url for the Verify and Facelist/Large Facelist operations
IMAGE_BASE_URL = 'https://csdx.blob.core.windows.net/resources/Face/Images/'
# </snippet_verify_baseurl>

# <snippet_persongroupvars>
# Used in the Person Group Operations,  Snapshot Operations, and Delete Person Group examples.
# You can call list_person_groups to print a list of preexisting PersonGroups.
# SOURCE_PERSON_GROUP_ID should be all lowercase and alphanumeric. For example, 'mygroupname' (dashes are OK).
PERSON_GROUP_ID = 'my-unique-person-group'

# Used for the Snapshot and Delete Person Group examples.
TARGET_PERSON_GROUP_ID = str(uuid.uuid4())  # assign a random ID (or name it anything)
# </snippet_persongroupvars>

# <snippet_snapshotvars>
'''
Snapshot operations variables
These are only used for the snapshot example. Set your environment variables accordingly.
'''
# Source endpoint, the location/subscription where the original person group is located.
SOURCE_ENDPOINT = ENDPOINT
# Source subscription key. Must match the source endpoint region.
SOURCE_KEY = os.environ['FACE_SUBSCRIPTION_KEY']
# Source subscription ID. Found in the Azure portal in the Overview page of your Face (or any) resource.
SOURCE_ID = os.environ['AZURE_SUBSCRIPTION_ID']
# Person group name that will get created in this quickstart's Person Group Operations example.
SOURCE_PERSON_GROUP_ID = PERSON_GROUP_ID
# Target endpoint. This is your 2nd Face subscription.
# TARGET_ENDPOINT = os.environ['FACE_ENDPOINT2']
TARGET_ENDPOINT = os.environ['FACE_ENDPOINT']
# Target subscription key. Must match the target endpoint region.
TARGET_KEY = os.environ['FACE_SUBSCRIPTION_KEY2']
# Target subscription ID. It will be the same as the source ID if created Face resources from the same 
# subscription (but moving from region to region). If they are differnt subscriptions, add the other target ID here.
TARGET_ID = os.environ['AZURE_SUBSCRIPTION_ID']
# NOTE: We do not need to specify the target PersonGroup ID here because we generate it with this example.
# Each new location you transfer a person group to will have a generated, new person group ID for that region.
# </snippet_snapshotvars>

'''
Authenticate
All examples use the same client, except for Snapshot Operations.
'''
# <snippet_auth>
# Create an authenticated FaceClient.
face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))
# </snippet_auth>
'''
END - Authenticate
'''

'''
Detect faces 
Detect faces in two images (get ID), draw rectangle around a third image.
'''
print('-----------------------------')
print()
print('DETECT FACES')
print()
# <snippet_detect>
# Detect a face in an image that contains a single face
single_face_image = 'human-753172_1280.jpg'
#single_image_name = os.path.basename(single_face_image_url)
# Group image for testing against

image = open(single_face_image, 'rb')

detected_faces = face_client.face.detect_with_stream(single_face_image)
if not detected_faces:
    raise Exception('No face detected from image {}'.format(single_image_name))

# Display the detected face ID in the first single-face image.
# Face IDs are used for comparison to faces (their IDs) detected in other images.
print('Detected face ID from', single_image_name, ':')
for face in detected_faces: print(face.face_id)
print()

# Save this ID for use in Find Similar
first_image_face_ID = detected_faces[0].face_id
# </snippet_detect>

# <snippet_detectgroup>
# Detect the faces in an image that contains multiple faces
# Each detected face gets assigned a new ID
multi_face_image_url = "http://www.historyplace.com/kennedy/president-family-portrait-closeup.jpg"
multi_image_name = os.path.basename(multi_face_image_url)
detected_faces2 = face_client.face.detect_with_url(url=multi_face_image_url)
# </snippet_detectgroup>

print('Detected face IDs from', multi_image_name, ':')
if not detected_faces2:
    raise Exception('No face detected from image {}.'.format(multi_image_name))
else:
    for face in detected_faces2:
        print(face.face_id)
print()

'''
Print image and draw rectangles around faces
'''
# <snippet_frame>
# Detect a face in an image that contains a single face
#single_face_image_url = 'https://raw.githubusercontent.com/Microsoft/Cognitive-Face-Windows/master/Data/detection1.jpg'
#single_face_image_url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Emotions-371238_640.jpg/1200px-Emotions-371238_640.jpg'
single_face_image_url = 'https://the-hollywood-gossip-res.cloudinary.com/iu/s--QNCk5CBP--/t_full/cs_srgb,f_auto,fl_strip_profile.lossy,q_auto:420/v1407739219/kim-kardashian-krying.jpg'
single_image_name = os.path.basename(single_face_image_url)
detected_faces = face_client.face.detect_with_url(url=single_face_image_url,
                                                  return_face_attributes=
                                                  [FaceAttributeType.age, FaceAttributeType.gender,
                                                   FaceAttributeType.facial_hair, FaceAttributeType.glasses,
                                                   FaceAttributeType.head_pose, FaceAttributeType.makeup,
                                                   FaceAttributeType.smile,
                                                   FaceAttributeType.emotion,
                                                   FaceAttributeType.accessories])
if not detected_faces:
    raise Exception('No face detected from image {}'.format(single_image_name))


# Convert width height to a point in a rectangle
def getRectangle(faceDictionary):
    rect = faceDictionary.face_rectangle
    left = rect.left
    top = rect.top
    right = left + rect.width
    bottom = top + rect.height

    return ((left, top), (right, bottom))


def getAttributeString(face_atrributes):
    attributes = ["recognized attrubutes"]
    attributes.append("age: " + str(face_atrributes.age))
    attributes.append("gender: " + face_atrributes.gender)
    for key, value in vars(face_atrributes.facial_hair).items():
        if not isinstance(value, dict):
            attributes.append(key + ": " + str(value))
    attributes.append("glasses: " + face_atrributes.glasses)
    attributes.append("hair: " + str(face_atrributes.hair))
    attributes.append("head pose: {" + str(face_atrributes.head_pose.pitch) + ", " +
                      str(face_atrributes.head_pose.roll) + ", " + str(face_atrributes.head_pose.yaw) + "}")
    for key, value in vars(face_atrributes.makeup).items():
        if not isinstance(value, dict):
            attributes.append(key + ": " + str(value))
    attributes.append("smile: " + str(face_atrributes.smile))
    for key, value in vars(face_atrributes.emotion).items():
        if not isinstance(value, dict):
                attributes.append(key + ": " + str(value))
    return attributes


def draw_multiple_line_text(draw_obj, lines_array, x_start, y_start):
    arialFont = ImageFont.truetype("arial", 10)
    y = y_start
    for line in lines_array:
        line_width, line_height = arialFont.getsize(line)
        draw_obj.text((x_start, y), line, fill='black', font=arialFont)
        y += line_height


# Download the image from the url
response = requests.get(single_face_image_url)
img = Image.open(BytesIO(response.content))

# For each face returned use the face rectangle and draw a red box.
print('Drawing rectangle around face... see popup for results.')
draw = ImageDraw.Draw(img)
for face in detected_faces:
    coords = getRectangle(face)
    lines = getAttributeString(face.face_attributes)
    draw.rectangle(coords, outline='red')
    bottom_x = coords[1][0]
    bottom_y = coords[0][1]
    draw.rectangle((bottom_x, bottom_y, bottom_x + 200, bottom_y + 300), fill='white')
    draw_multiple_line_text(draw, lines, bottom_x, bottom_y)
    #draw.text((coords[1][0], coords[1][1]), "hello", font=ImageFont.truetype("arial", 16))
    #text = textwrap.fill("test ", width=35)

# Display the image in the users default image browser.
img.show()
# </snippet_frame>

print()
'''
END - Detect faces
'''
