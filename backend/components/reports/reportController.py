import base64
import io
import os
from collections import Counter

from flask import Blueprint, request, jsonify, render_template, make_response, send_file, current_app
from xhtml2pdf import pisa
from xhtml2pdf.files import pisaFileObject
from backend.components.reports.reportService import get_report_data
from datetime import datetime

bp = Blueprint('reports', __name__, url_prefix='/api/raport')


@bp.route('', methods=['GET'])
def generate_report():
    """
        Retrieves worker entry reports based on provided filters.

        This endpoint allows filtering entries (Entry) by date, worker, and validation status (valid/invalid).
        Returns data in JSON format (including Base64 encoded face image), which can be used to generate tables or PDF files.

        **Parameters**:
        - `date_from` (str): Start date of the range (format YYYY-MM-DD or ISO). Optional.
        - `date_to` (str): End date of the range (format YYYY-MM-DD or ISO). If only date is provided, it covers the whole day (until 23:59:59). Optional.
        - `pracownik_id` (int): Worker ID to filter by. Optional.
        - `wejscia_niepoprawne` (bool): Flag - if present, includes invalid entries (error code != 0).
        - `wejscia_poprawne` (bool): Flag - if present, includes valid entries (error code == 0).

        **Returns**:
        - `JSON` - Object containing count, filters used, calculated statistics, and the list of entry data.

        ---
        tags:
          - Reports
        parameters:
          - name: date_from
            in: query
            type: string
            required: false
            description: Start date of the range (format YYYY-MM-DD or ISO).
          - name: date_to
            in: query
            type: string
            required: false
            description: End date of the range (format YYYY-MM-DD or ISO). If only date is provided, covers the whole day (until 23:59:59).
          - name: pracownik_id
            in: query
            type: integer
            required: false
            description: Worker ID to filter by.
          - name: wejscia_niepoprawne
            in: query
            type: string
            required: false
            allowEmptyValue: true
            description: >
              Presence flag. If this parameter is included in the URL (regardless of its value),
              invalid entries (error code != 0) will be included in the report.
          - name: wejscia_poprawne
            in: query
            type: string
            required: false
            allowEmptyValue: true
            description: >
              Presence flag. If this parameter is included in the URL (regardless of its value),
              valid entries (error code == 0) will be included in the report.
        responses:
          200:
            description: Report successfully generated.
            schema:
              type: object
              properties:
                count:
                  type: integer
                  description: Number of entries found.
                filters:
                  type: object
                  description: Filters used in the query.
                statistics:
                  type: object
                  description: Aggregated statistics for the selected period.
                  properties:
                    total_entries:
                      type: integer
                      description: Total number of entries in the result set.
                    valid_entries:
                      type: integer
                      description: Number of successful entries (code 0).
                    invalid_entries:
                      type: integer
                      description: Number of failed entries (code != 0).
                    success_rate_percent:
                      type: number
                      format: float
                      description: Percentage of valid entries.
                    most_invalid_attempts_worker:
                      type: object
                      description: Worker with the most invalid attempts.
                      properties:
                        name:
                          type: string
                        count:
                          type: integer
                    most_valid_entries_worker:
                      type: object
                      description: Worker with the most valid entries.
                      properties:
                        name:
                          type: string
                        count:
                          type: integer
                    daily_traffic:
                      type: object
                      description: Dictionary mapping dates (YYYY-MM-DD) to entry counts.
                      additionalProperties:
                        type: integer
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
                        description: Response code (0 = success).
                      message:
                        type: string
                      worker_id:
                        type: integer
                      worker_name:
                        type: string
                      face_image:
                        type: string
                        description: Base64 encoded face image (or null).
          400:
            description: Parameter validation error.
          500:
            description: Internal server error.
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

        data, statistics = _calculate_statistics(results)
        json_data = []

        for item in data:
            # Kodowanie obrazu do Base64
            encoded_image = None
            if item['face_image_bytes']:
                encoded_image = base64.b64encode(item['face_image_bytes']).decode('utf-8')

            json_data.append({
                **item,
                'date': item['date'].isoformat(),
                'face_image': encoded_image, # obraz base64 # @TODO - zmioana str na base64 usunąć ""
                'face_image_bytes': None  # Nie wysyłamy bajtów w JSON
            })

        return jsonify({
            'count': len(json_data),
            'filters': {
                'date_from': date_from_str,
                'date_to': date_to_str,
                'worker_id': worker_id,
                'show_valid': show_valid,
                'show_invalid': show_invalid
            },
            'statistics': statistics,
            'data': json_data
        })

    except Exception as e:
        print(f"Błąd raportu: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/pdf', methods=['GET'])
def generate_pdf_report():
    """
        Generates a report in PDF format based on provided filters.

        Retrieves exactly the same parameters as the JSON version.

        **Parameters**:
        - `date_from` (str): Start date of the range (format YYYY-MM-DD or ISO). Optional.
        - `date_to` (str): End date of the range (format YYYY-MM-DD or ISO). Optional.
        - `pracownik_id` (int): Worker ID to filter by. Optional.
        - `wejscia_niepoprawne` (bool): Flag - if present, includes invalid entries.
        - `wejscia_poprawne` (bool): Flag - if present, includes valid entries.

        **Returns**:
        - `application/pdf` - A downloadable PDF file.

        ---
        tags:
          - Reports
        parameters:
          - name: date_from
            in: query
            type: string
            required: false
            description: Start date of the range (format YYYY-MM-DD or ISO).
          - name: date_to
            in: query
            type: string
            required: false
            description: End date of the range (format YYYY-MM-DD or ISO).
          - name: pracownik_id
            in: query
            type: integer
            required: false
            description: Worker ID to filter by.
          - name: wejscia_niepoprawne
            in: query
            type: boolean
            required: false
            allowEmptyValue: true
            description: Flag - if present, includes invalid entries.
          - name: wejscia_poprawne
            in: query
            type: boolean
            required: false
            allowEmptyValue: true
            description: Flag - if present, includes valid entries.
        responses:
          200:
            description: PDF report generated successfully.
            content:
              application/pdf:
                schema:
                  type: string
                  format: binary
          400:
            description: Parameter validation error.
          500:
            description: Internal server error.
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
                # Jeśli podano samą datę (format YYYY-MM-DD, bez godziny), ustawiamy czas na koniec dnia,
                # aby uwzględnić wszystkie wpisy z tego dnia (domyślnie fromisoformat ustawia 00:00:00).
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

        # --- 3. Przygotowanie danych dla szablonu HTML (z użyciem funkcji pomocniczej) ---
        data, statistics = _calculate_statistics(results)

        report_data = []
        for item in data:
            # Konwersja obrazka na Base64 (dla HTML)
            img_b64 = None
            if item['face_image_bytes']:
                img_b64 = base64.b64encode(item['face_image_bytes']).decode('utf-8')

            report_data.append({
                'id': item['id'],
                'date': item['date'].strftime('%Y-%m-%d %H:%M:%S'),
                'code': item['code'],
                'message': item['message'],
                'worker_id': item['worker_id'],
                'worker_name': item['worker_name'],
                'face_image_b64': img_b64
            })

        font_path = os.path.join(current_app.config['STATIC_FOLDER'], 'fonts', 'Roboto-Regular.ttf')

        context = {
            'data': report_data,
            'count': statistics['total_entries'],
            'statistics': statistics,
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

        # On windows, file paths to the font break
        # known issue, applying a monkeypatch
        # https://github.com/xhtml2pdf/xhtml2pdf/issues/623#issuecomment-1372719452
        pisaFileObject.getNamedFile = lambda self: self.uri
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

def _calculate_statistics(results):
    """
    Funkcja pomocnicza do obliczania statystyk na podstawie wyników.
    Używana zarówno przez endpoint JSON, jak i PDF.
    """
    stats_total = 0
    stats_valid = 0
    stats_invalid = 0

    daily_counter = Counter()
    cheater_counter = Counter()
    top_worker_counter = Counter()

    processed_data = []

    for entry, worker in results:
        stats_total += 1
        worker_name = worker.name if worker else f'Nieznany (ID: {entry.worker_id})'
        day_str = entry.date.strftime('%Y-%m-%d')

        # 1. Statystyki dzienne
        daily_counter[day_str] += 1

        # 2. Statystyki poprawności
        if entry.code == 0:
            stats_valid += 1
            top_worker_counter[worker_name] += 1
        else:
            stats_invalid += 1
            cheater_counter[worker_name] += 1

        # Przygotowanie danych do listy (bez kodowania obrazka, enpoint zwracający JSON zajmuje się konwersją do base64)
        entry_data = {
            'id': entry.id,
            'date': entry.date,
            'code': entry.code,
            'message': entry.message,
            'worker_id': entry.worker_id,
            'worker_name': worker_name,
            'face_image_bytes': entry.face_image # Surowe bajty
        }
        processed_data.append(entry_data)

    # --- Finalne statystyki ---
    most_cheating = cheater_counter.most_common(1)
    most_cheating_data = {'name': most_cheating[0][0], 'count': most_cheating[0][1]} if most_cheating else None

    most_active = top_worker_counter.most_common(1)
    most_active_data = {'name': most_active[0][0], 'count': most_active[0][1]} if most_active else None

    sorted_daily_traffic = dict(sorted(daily_counter.items()))

    statistics = {
        'total_entries': stats_total,
        'valid_entries': stats_valid,
        'invalid_entries': stats_invalid,
        'success_rate_percent': round((stats_valid / stats_total * 100), 2) if stats_total > 0 else 0,
        'most_invalid_attempts_worker': most_cheating_data,
        'most_valid_entries_worker': most_active_data,
        'daily_traffic': sorted_daily_traffic
    }

    return processed_data, statistics