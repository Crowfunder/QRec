import face_recognition
from backend.database.models import Worker

def verifyWorkerFace(worker: Worker, ):
    '''
    original_image = worker.getFace()
    checked_image = checked_image (param)
    original_encoding = face_recognition.face_encodings(original_image)[0]
    unknown_encoding = face_recognition.face_encodings(checked_image)[0]
    # todo: moze encoding powinien być przechowywany w db zamiast obrazka?

    results = face_recognition.compare_faces([biden_encoding], unknown_encoding)
    '''