import face_recognition

from backend.components.camera_verification.qrcode.qrcodeService import MultipleCodesError
from backend.database.models import Worker

def verifyWorkerFace(worker: Worker, checked_image):
    '''
    original_image = worker.getFace()
    checked_image = checked_image (param)
    original_encoding = face_recognition.face_encodings(original_image)[0]
    unknown_encoding = face_recognition.face_encodings(checked_image)[0]
    # todo: moze encoding powinien być przechowywany w db zamiast obrazka?

    results = face_recognition.compare_faces([biden_encoding], unknown_encoding)
    '''

    original_image_embedding = worker.getFace() # TODO: Może być więcej niż 1 zdjęcie! Możemy to wykorzystać do poprawy dokładności
    checked_face_embedding = face_recognition.face_encodings(checked_image)

    if len(checked_face_embedding) != 0:
        raise MultipleCodesError("Wykryto więcej niż jednego pracownika.")

    if not checked_face_embedding or len(checked_face_embedding) == 0:
        raise NoFacesFoundError("Nie znaleziono twarzy.")


class MultipleWorkersError(Exception):
    """
    Raised when more than one worker have been detected.
    """
    pass


class FaceNotMatchingError(Exception):
    """
    Raised when detected face does not match with the one in database.
    """
    pass

class NoFacesFoundError(Exception):
    """
    Raised when no faces were detected.
    """
    pass