import os
import cv2
import threading
import pickle
import numpy as np
from twilio.rest import Client
import requests
import face_recognition
from flask_app import app, current_location
import time
from waitress import serve
from pymongo import MongoClient
import datetime

# Database Connection
client = MongoClient("mongodb+srv://nihalshetty0206:<db_password>@cluster0.woc0o.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["mydatabase"]
collection = db["mycollection"]

# Twilio credentials
account_sid = 'AC4d7be629b050550eda775da5f719c61f'
auth_token = 'eb82220ac98570cdff2f58a46a32054f'
twilio_phone_number = '+18313876388'
manager_number = '+918310654643'

# Employee Data (Index Mapping)
employee_data = {
    0: {"name": "Nagesh", "employee_id": "CS090", "department": "CSE"},
    1: {"name": "Nihal", "employee_id": "CS095", "department": "CSE"},
}

# Mapping Employee Index to Phone Numbers
employee_contact = {
    0: "+918861167234",  # nageh phone number
    1: "+918546964512",  # Nihal phone number

}

# Facial Recognition Setup
print("Loading encode file")
if not os.path.exists("EncodeFile.p"):
    print("Encoding file not found!")
    exit()
with open("EncodeFile.p", 'rb') as file:
    encodeListKnownWithIds = pickle.load(file)
encodeListKnown, studentIds = encodeListKnownWithIds
print("Encode file loaded")

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(3, 640)
cap.set(4, 480)

if not os.path.exists("Unrecognized"):
    os.makedirs("Unrecognized")

alerted_faces = set()

def get_ngrok_url():
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels")
        if response.status_code == 200:
            tunnels = response.json()["tunnels"]
            return tunnels[0]["public_url"]
    except Exception as e:
        print(f"Error while fetching Ngrok URL: {e}")
    return None

def send_sms(link, to_number):
    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=f"Click this link to share your location: {link}",
            from_=twilio_phone_number,
            to=to_number
        )
        print(f"Message sent successfully! SID: {message.sid}")
    except Exception as e:
        print(f"Failed to send SMS: {e}")

def wait_for_coordinates():
    while current_location["latitude"] is None or current_location["longitude"] is None:
        time.sleep(1)
    print("Coordinates fetched successfully!")

def validate_location():
    tolerance = 0.001
    target_lat, target_lon = 13.0512775, 74.9648971
    if (
        abs(current_location["latitude"] - target_lat) <= tolerance and
        abs(current_location["longitude"] - target_lon) <= tolerance
    ):
        return "Within location"
    return "within location"

def store_employee_data(index, status):
    if index in employee_data:
        employee = employee_data[index]
        attendance_record = {
            "name": employee["name"],
            "employee_id": employee["employee_id"],
            "department": employee["department"],
            "timestamp": datetime.datetime.now(),
            "status": "within location"
        }
        try:
            collection.insert_one(attendance_record)
            print(f"Employee data stored successfully: {attendance_record}")
        except Exception as e:
            print(f"Failed to store employee data: {e}")
    else:
        print(f"No employee data found for index: {index}")

face_status = {}

def process_frame():
    while True:
        success, img = cap.read()
        if not success:
            continue

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

            matchIndex = np.argmin(faceDis)
            if matches[matchIndex]:
                print(f"Known face detected, index: {matchIndex}")

                if matchIndex not in face_status:
                    face_status[matchIndex] = {"sms_sent": False, "data_stored": False}

                if not face_status[matchIndex]["sms_sent"]:
                    current_location["latitude"] = None
                    current_location["longitude"] = None

                    if matchIndex in employee_contact:
                        recipient_number = employee_contact[matchIndex]
                        ngrok_url = get_ngrok_url()
                        if ngrok_url:
                            location_link = f"{ngrok_url}/share_location"
                            send_sms(location_link, recipient_number)
                            print("Waiting for coordinates to be fetched...")
                            wait_for_coordinates()

                            location_status = validate_location()
                            if location_status == "Within location":
                                print("Employee is within the location.")
                            else:
                                send_sms("Employee not within location", manager_number)

                        face_status[matchIndex]["sms_sent"] = True

                if not face_status[matchIndex]["data_stored"]:
                    location_status = validate_location()
                    store_employee_data(matchIndex, location_status)
                    face_status[matchIndex]["data_stored"] = True
            else:
                print("Unrecognized face detected")
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4

                face_hash = hash(tuple(encodeFace))
                if face_hash not in alerted_faces:
                    alerted_faces.add(face_hash)
                    unrecogFace = img[y1:y2, x1:x2]
                    if unrecogFace.size != 0:
                        file_name = f'Unrecognized/{str(len(os.listdir("Unrecognized")))}.jpg'
                        cv2.imwrite(file_name, unrecogFace)
                        send_sms("Unrecognized face detected! Check the captured image.", manager_number)

        cv2.imshow("Face Recognition", img)
        cv2.waitKey(1)

def run_flask_app():
    serve(app, host='0.0.0.0', port=5000)

flask_thread = threading.Thread(target=run_flask_app, daemon=True)
flask_thread.start()

process_frame()
