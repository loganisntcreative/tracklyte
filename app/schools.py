from flask import Blueprint, request, jsonify
import urllib.request
import urllib.parse
import json

schools_bp = Blueprint('schools', __name__)


@schools_bp.route('/api/schools')
def search_schools():
    query = request.args.get('q', '').strip()
    school_type = request.args.get('type', 'k12')

    if len(query) < 2:
        return jsonify([])

    try:
        encoded = urllib.parse.quote(query)

        if school_type == 'college':
            url = (
                f"https://educationdata.urban.org/api/v1/college-university/"
                f"ipeds/directory/?inst_name={encoded}&per_page=10"
                f"&fields=inst_name,city,state_abbr"
            )
            name_key = 'inst_name'
            state_key = 'state_abbr'
        else:
            url = (
                f"https://educationdata.urban.org/api/v1/schools/ccd/"
                f"directory/?school_name={encoded}&per_page=10"
                f"&fields=school_name,city,state_code&school_level=3"
            )
            name_key = 'school_name'
            state_key = 'state_code'

        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; TrackLyte/1.0)',
                'Accept': 'application/json'
            }
        )

        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode())

        results = []
        seen = set()

        for school in data.get('results', []):
            name = (school.get(name_key) or '').strip().title()
            city = (school.get('city') or '').strip().title()
            state = (school.get(state_key) or '').strip()

            if not name or name in seen:
                continue
            seen.add(name)
            display = f"{name} — {city}, {state}" if city and state else name
            results.append({'name': name, 'display': display})

        return jsonify(results)

    except Exception as e:
        print(f'School search error: {e}')
        return jsonify([])


@schools_bp.route('/api/schools/test')
def test():
    return jsonify({'status': 'ok', 'message': 'Schools API is reachable'})