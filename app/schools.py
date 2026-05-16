from flask import Blueprint, request, jsonify
import urllib.request
import json

schools_bp = Blueprint('schools', __name__)

@schools_bp.route('/api/schools')
def search_schools():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])

    try:
        url = (
            f"https://educationdata.urban.org/api/v1/schools/ccd/directory/2021/"
            f"?school_name={urllib.parse.quote(query)}&per_page=10&fields=school_name,city,state_code"
        )
        import urllib.parse
        url = (
            f"https://educationdata.urban.org/api/v1/schools/ccd/directory/2021/"
            f"?school_name={urllib.parse.quote(query)}&per_page=10&fields=school_name,city,state_code"
        )
        req = urllib.request.Request(url, headers={'User-Agent': 'TrackLyte/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

        results = []
        seen = set()
        for school in data.get('results', []):
            name = school.get('school_name', '').title()
            city = school.get('city', '').title()
            state = school.get('state_code', '')
            display = f"{name} — {city}, {state}"
            if name not in seen:
                seen.add(name)
                results.append({'name': name, 'display': display})

        return jsonify(results)
    except Exception as e:
        return jsonify([])