from backend.components.camera_verification.qrcode.qrcodeService import (
    InvalidCodeError, QRCodeError, MultipleCodesError, NoCodeFoundError
)
from backend.components.camera_verification.faceid.faceidService import (
    MultipleWorkersError, NoFacesFoundError, FaceNotMatchingError, FaceIDError
)

class ErrorResponse:
    def __init__(self, code, message, logged=True):
        self.code = code
        self.message = message
        self.logged = logged
        
    def asdict(self):
        return {
            'code': self.code,
            'message': self.message,
            'logged': self.logged,
        }
        

EXCEPTION_MAP = {
    Exception                : ErrorResponse(-1, "Nieznany błąd, poinformuj producenta."),
    type(None)               : ErrorResponse(0, "Weryfikacja udana."),
    NoCodeFoundError         : ErrorResponse(1, "Puste zdjęcie. Nie wykryto kodu QR.", logged=False),
    NoFacesFoundError        : ErrorResponse(2, "Puste zdjęcie. Nie wykryto twarzy.", logged=False),
    QRCodeError              : ErrorResponse(10, "Ogólny błąd kodu QR."),
    InvalidCodeError         : ErrorResponse(11, "Podany kod QR jest niepoprawny."),
    MultipleCodesError       : ErrorResponse(12, "Podano więcej niż jeden kod QR."),
    FaceIDError              : ErrorResponse(20, "Ogólny błąd weryfikacji twarzy."),
    FaceNotMatchingError     : ErrorResponse(21, "Wykryta twarz nie pasuje do kodu QR."),
    MultipleWorkersError     : ErrorResponse(22, "Wykryto więcej niż jednego pracownika."),
}