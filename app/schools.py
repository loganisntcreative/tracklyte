from flask import Blueprint, request, jsonify
from app.schools_data import HIGH_SCHOOLS, COLLEGES
from app import cache

schools_bp = Blueprint('schools', __name__)

# Pre-lowercase at module level — runs ONCE on startup, not on every request
_HIGH_SCHOOLS_LC = [(s, s.lower()) for s in HIGH_SCHOOLS]
_COLLEGES_LC = [(s, s.lower()) for s in COLLEGES]
_ALL_LC = _HIGH_SCHOOLS_LC + _COLLEGES_LC


def _search(dataset, query, limit=15):
    results = []
    seen = set()
    for original, lower in dataset:
        if query in lower and original not in seen:
            seen.add(original)
            results.append({'name': original, 'display': original})
            if len(results) >= limit:
                break
    return results


@schools_bp.route('/api/schools')
@cache.cached(timeout=3600, key_prefix=lambda: f"schools_{request.args.get('q','').strip().lower()}_{request.args.get('type','k12')}")
def search_schools():
    query = request.args.get('q', '').strip().lower()
    school_type = request.args.get('type', 'k12')

    if len(query) < 2:
        return jsonify([])

    if school_type == 'college':
        dataset = _COLLEGES_LC
    elif school_type == 'all':
        dataset = _ALL_LC
    else:
        dataset = _HIGH_SCHOOLS_LC

    return jsonify(_search(dataset, query))