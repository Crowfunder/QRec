import base64
import io
import os
from flask import Blueprint, request, jsonify, render_template, make_response, send_file, current_app
from xhtml2pdf import pisa
from backend.components.reports.reportService import get_report_data
from datetime import datetime

bp = Blueprint('reports', __name__, url_prefix='/api/raport')


@bp.route('', methods=['GET'])
def generate_report():
    """
    Pobiera raport wejść pracowników na podstawie zadanych filtrów.

    Endpoint ten pozwala na filtrowanie wpisów (Entry) po dacie, pracowniku oraz statusie walidacji (poprawne/niepoprawne).
    Zwraca dane w formacie JSON (w tym obraz twarzy zakodowany w Base64), które mogą posłużyć do wygenerowania tabeli lub pliku PDF.

    ---
    tags:
      - Raporty
    parameters:
      - name: date_from
        in: query
        type: string
        required: false
        description: Data początkowa zakresu (format YYYY-MM-DD lub ISO).
      - name: date_to
        in: query
        type: string
        required: false
        description: Data końcowa zakresu (format YYYY-MM-DD lub ISO). Jeśli podano samą datę, obejmuje ona cały dzień (do 23:59:59).
      - name: pracownik_id
        in: query
        type: integer
        required: false
        description: ID pracownika do filtrowania.
      - name: wejscia_niepoprawne
        in: query
        type: boolean
        required: false
        allowEmptyValue: true
        description: Flaga - jeśli obecna, uwzględnia wejścia niepoprawne (kod błędu != 0).
      - name: wejscia_poprawne
        in: query
        type: boolean
        required: false
        allowEmptyValue: true
        description: Flaga - jeśli obecna, uwzględnia wejścia poprawne (kod == 0).
    responses:
      200:
        description: Pomyślnie wygenerowano raport.
        schema:
          type: object
          properties:
            count:
              type: integer
              description: Liczba znalezionych wpisów.
            filters:
              type: object
              description: Filtry użyte w zapytaniu.
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  date:
                    type: string
                    format: date-time
                  code:
                    type: integer
                    description: Kod odpowiedzi (0 = sukces).
                  message:
                    type: string
                  worker_id:
                    type: integer
                  worker_name:
                    type: string
                  face_image:
                    type: string
                    description: Obraz twarzy zakodowany w Base64 (lub null).
      400:
        description: Błąd walidacji parametrów.
      500:
        description: Wewnętrzny błąd serwera.
    """
    try:
        date_from_str = request.args.get('date_from')
        date_to_str = request.args.get('date_to')
        worker_id = request.args.get('pracownik_id', type=int)

        show_invalid = 'wejscia_niepoprawne' in request.args
        show_valid = 'wejscia_poprawne' in request.args

        date_from = None
        date_to = None

        if date_from_str:
            try:
                date_from = datetime.fromisoformat(date_from_str)
            except ValueError:
                return jsonify({'error': 'Nieprawidłowy format date_from. Oczekiwano YYYY-MM-DD'}), 400

        if date_to_str:
            try:
                date_to = datetime.fromisoformat(date_to_str)
                if len(date_to_str) == 10:
                    date_to = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)
            except ValueError:
                return jsonify({'error': 'Nieprawidłowy format date_to'}), 400

        results = get_report_data(
            date_from=date_from,
            date_to=date_to,
            worker_id=worker_id,
            show_valid=show_valid,
            show_invalid=show_invalid
        )

        report_data = []
        for entry, worker in results:
            # Kodowanie obrazu do Base64
            encoded_image = None
            if entry.face_image:
                encoded_image = base64.b64encode(entry.face_image).decode('utf-8')

            report_data.append({
                'id': entry.id,
                'date': entry.date.isoformat(),
                'code': entry.code,
                'message': entry.message,
                'worker_id': entry.worker_id,
                'worker_name': worker.name if worker else 'Nieznany',
                'face_image': encoded_image  # Dodane pole
            })

        return jsonify({
            'count': len(report_data),
            'filters': {
                'date_from': date_from_str,
                'date_to': date_to_str,
                'worker_id': worker_id,
                'show_valid': show_valid,
                'show_invalid': show_invalid
            },
            'data': report_data
        })

    except Exception as e:
        print(f"Błąd raportu: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/pdf', methods=['GET'])
def generate_pdf_report():
    """
    Generuje raport w formacie PDF na podstawie zadanych filtrów.
    Pobiera dokładnie te same parametry co wersja JSON.
    """
    try:
        date_from_str = request.args.get('date_from')
        date_to_str = request.args.get('date_to')
        worker_id = request.args.get('pracownik_id', type=int)

        show_invalid = 'wejscia_niepoprawne' in request.args
        show_valid = 'wejscia_poprawne' in request.args

        date_from = None
        date_to = None

        if date_from_str:
            try:
                date_from = datetime.fromisoformat(date_from_str)
            except ValueError:
                return jsonify({'error': 'Nieprawidłowy format date_from'}), 400

        if date_to_str:
            try:
                date_to = datetime.fromisoformat(date_to_str)
                if len(date_to_str) == 10:
                    date_to = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)
            except ValueError:
                return jsonify({'error': 'Nieprawidłowy format date_to'}), 400

        # --- 2. Pobranie danych ---
        results = get_report_data(
            date_from=date_from,
            date_to=date_to,
            worker_id=worker_id,
            show_valid=show_valid,
            show_invalid=show_invalid
        )

        # --- 3. Przygotowanie danych dla szablonu HTML ---
        report_data = []
        for entry, worker in results:
            # Konwersja obrazka na Base64 (dla HTML)
            img_b64 = None
            if entry.face_image:
                img_b64 = base64.b64encode(entry.face_image).decode('utf-8')

            report_data.append({
                'id': entry.id,
                'date': entry.date.strftime('%Y-%m-%d %H:%M:%S'),
                'code': entry.code,
                'message': entry.message,
                'worker_id': entry.worker_id,
                'worker_name': worker.name if worker else 'Nieznany',
                'face_image_b64': img_b64
            })

        font_path = os.path.join(current_app.config['STATIC_FOLDER'], 'fonts', 'Roboto-Regular.ttf')

        context = {
            'data': report_data,
            'count': len(report_data),
            'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'filters': {
                'date_from': date_from_str,
                'date_to': date_to_str,
                'worker_id': worker_id,
                'show_valid': show_valid,
                'show_invalid': show_invalid
            },
            'font_path': font_path
        }

        # --- 4. Renderowanie HTML i konwersja na PDF ---
        html_content = render_template('reports/report_pdf.html', **context)

        pdf_output = io.BytesIO()
        pisa_status = pisa.CreatePDF(
            io.BytesIO(html_content.encode('utf-8')),
            dest=pdf_output,
            encoding='utf-8'
        )

        if pisa_status.err:
            return jsonify({'error': 'Błąd podczas generowania PDF'}), 500

        pdf_output.seek(0)

        return send_file(
            pdf_output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"raport_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        )

    except Exception as e:
        print(f"Błąd generowania PDF: {e}")
        return jsonify({'error': str(e)}), 500