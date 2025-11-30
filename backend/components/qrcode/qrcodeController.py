import numpy as np
import cv2
from flask import Blueprint, request, jsonify
from backend.components.qrcode.qrcodeService import (
    decodeQRImage,
    getWorkerByQRCodeSecret,
    QRCodeError,
    MultipleCodesError,
    NoCodeFoundError
)


bp = Blueprint('bp_qrcode', __name__)


@bp.route('/test', methods=['GET'])
def test():

    return 'ok', 200


@bp.route('/api/qrcode/decodeToWorker', methods=['POST'])
def getWorkerFromQRCode():
    """
        Identyfikacja pracownika na podstawie zdjęcia kodu QR.
        ---
        tags:
          - QRCode
        summary: Dekoduje przesłany obraz QR i zwraca dane pracownika.
        description: >
          Przyjmuje plik obrazu (multipart/form-data), dekoduje zawarty w nim kod QR,
          wyszukuje powiązanego pracownika w bazie danych i zwraca jego dane.
        consumes:
          - multipart/form-data
        parameters:
          - in: formData
            name: file
            type: file
            required: true
            description: Obraz zawierający kod QR do zdekodowania.
        responses:
          200:
            description: Pomyślnie zidentyfikowano pracownika.
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                message:
                  type: string
                  example: 'Pomyślnie zidentyfikowano pracownika.'
                worker:
                  type: object
                  description: Obiekt z danymi pracownika (struktura zależy od metody worker.to_dict()).
                  properties:
                    id:
                      type: integer
                      example: 123
                    name:
                      type: string
                      example: "Jan Kowalski"
                    face_image:
                        type: string
                    expitration_date:
                        type: datetime
                    secret:
                      type: string
          400:
            description: Błąd walidacji lub dekodowania (brak pliku, pusty plik, nieczytelny QR).
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: 'Brak pliku w żądaniu (oczekiwano klucza "file").'
          404:
            description: Nie znaleziono pracownika dla podanego kodu QR.
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: 'Nie znaleziono pracownika powiązanego z tym kodem QR.'
          500:
            description: Wewnętrzny błąd serwera.
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: 'Wystąpił błąd podczas przetwarzania żądania.'
        """
    if 'file' not in request.files:
        return jsonify({'error': 'Brak pliku w żądaniu (oczekiwano klucza "file").'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Nie wybrano pliku.'}), 400

    try:
        qr_secret = decodeQRImage(file.stream)

        worker = getWorkerByQRCodeSecret(qr_secret)

        if not worker:
            return jsonify({'error': 'Nie znaleziono pracownika powiązanego z tym kodem QR.'}), 404

        worker_data = worker.to_dict()

        return jsonify({
            'success': True,
            'message': 'Pomyślnie zidentyfikowano pracownika.',
            'worker': worker_data
        }), 200

    except (MultipleCodesError, NoCodeFoundError, ValueError) as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        print(f"Critical Error in QR Controller: {e}")
        return jsonify({'error': 'Wystąpił błąd podczas przetwarzania żądania.'}), 500