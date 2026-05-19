from flask import Blueprint, request, jsonify
from app.schools_data import HIGH_SCHOOLS, COLLEGES

schools_bp = Blueprint('schools', __name__)

@schools_bp.route('/api/schools')
def search_schools():
    query = request.args.get('q', '').strip().lower()
    school_type = request.args.get('type', 'k12')

    if len(query) < 2:
        return jsonify([])

    if school_type == 'college':
        dataset = COLLEGES
    elif school_type == 'k12':
        dataset = HIGH_SCHOOLS
    else:
        dataset = HIGH_SCHOOLS + COLLEGES

    results = []
    seen = set()
    for school in dataset:
        if query in school.lower() and school not in seen:
            seen.add(school)
            results.append({'name': school, 'display': school})
        if len(results) >= 10:
            break

    return jsonify(results)


@schools_bp.route('/api/schools/test')
def test():
    return jsonify({
        'status': 'ok',
        'k12_count': len(HIGH_SCHOOLS),
        'college_count': len(COLLEGES)
    })