import dlib
import numpy as np
import face_recognition_models
from sklearn.svm import SVC
import streamlit as st

from src.database.db import get_all_students


@st.cache_resource
def load_dlib_models():
    detector = dlib.get_frontal_face_detector()     #Detects all faces in images

    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()     #Finds facial landmarks.
    )

    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()   #Face Embedding (Neural Network)     
    )

    return detector, sp, facerec



def get_face_embedding(image_np):
    detector, sp, facerec = load_dlib_models()
    faces = detector(image_np, 1)       #Total Faces in Images(Input- Classroom Image)

    encodings = []          #Contains Embeddings of each student face

    for face in faces:
        shape = sp(image_np, face)      #Gets 68 facial points.
        face_descriptor = facerec.compute_face_descriptor(image_np, shape, 1)    #128 Embedding

        encodings.append(np.array(face_descriptor))     
    return encodings


@st.cache_resource
def get_trained_model():
    X = []      #Stores Embedding
    y = []      #Stores Labels(Id)

    student_db = get_all_students()        #Gets all students ID and Embedding stores in supabase

    if not student_db:
        return None

    for student in student_db:
        embedding = student.get('face_embedding')
        if embedding:
            X.append(np.array(embedding))
            y.append(student.get('student_id'))

    if len(X) == 0:
        return None

    clf = SVC(kernel="linear", probability=True, class_weight="balanced")



    try:
        clf.fit(X,y)        #Model Training
    except ValueError:
        pass

    return {'clf':clf, 'X' : X, 'y': y}


def train_clf():        #retrain Model
    st.cache_resource.clear()
    model_data = get_trained_model()
    return bool(model_data)


def predict_attendance(class_img_np):
    encodings = get_face_embedding(class_img_np)        #Gets Embedding of all students present in photo

    detected_student = {}

    model_data = get_trained_model()

    if not model_data:
        return detected_student, [], len(encodings)
    
    clf = model_data['clf']
    X_train = model_data['X']
    y_train = model_data['y']


    all_students = sorted(list(set(y_train)))


    for encoding in encodings:
        if len(all_students) >= 2:
            predicted_id = int(clf.predict([encoding])[0])

        else:
            predicted_id = int(all_students[0])


        student_embedding = X_train[y_train.index(predicted_id)]

        best_match_score = np.linalg.norm(student_embedding - encoding)

        recognition_threshold = 0.6

        if best_match_score <= recognition_threshold:
            detected_student[predicted_id] = True

    return detected_student, all_students, len(encodings)