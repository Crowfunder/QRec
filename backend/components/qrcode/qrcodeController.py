from flask import Blueprint


bp = Blueprint('bp_qrcode', __name__)


@bp.route('/test', methods=['GET'])
def test():

    return 'ok', 200

    