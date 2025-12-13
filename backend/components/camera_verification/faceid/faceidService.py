import face_recognition

from backend.components.camera_verification.qrcode.qrcodeService import MultipleCodesError
from backend.database.models import Worker
from backend.components.workers.workerService import getWorkerEmbedding

def verifyWorkerFace(worker: Worker, checked_image):
    '''
    # todo: moze encoding powinien być przechowywany w db zamiast obrazka?
    # TODO: Może być więcej niż 1 zdjęcie! Możemy to wykorzystać do poprawy dokładności
    '''

    original_image_embedding = getWorkerEmbedding(worker)
    try: checked_face_embedding = face_recognition.face_encodings(checked_image)
    except Exception as e:
        raise FaceIDError(str(e))

    if len(checked_face_embedding) != 0:
        raise MultipleCodesError("Wykryto więcej niż jednego pracownika.")

    if not checked_face_embedding or len(checked_face_embedding) == 0:
        raise NoFacesFoundError("Nie znaleziono twarzy.")

    try: faces_match = face_recognition.compare_faces(original_image_embedding, checked_face_embedding)
    except Exception as e:
        raise FaceIDError(str(e))

    if not faces_match:
        raise FaceNotMatchingError("Niezgodność zeskanowanej twarzy")

    return faces_match


class FaceIDError(Exception):
    """
    Base class for face id errors
    """
    pass

class MultipleWorkersError(FaceIDError):
    """
    Raised when more than one worker have been detected.
    """
    pass

class FaceNotMatchingError(FaceIDError):
    """
    Raised when detected face does not match with the one in database.
    """
    pass

class NoFacesFoundError(FaceIDError):
    """
    Raised when no faces were detected.
    """
    pass