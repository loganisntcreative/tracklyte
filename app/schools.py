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
        if school_type == 'college':
            url = (
                f"https://educationdata.urban.org/api/v1/college-university/ipeds/directory/2020/"
                f"?inst_name={urllib.parse.quote(query)}&per_page=10"
                f"&fields=inst_name,city,state_abbr"
            )
        else:
            url = (
                f"https://educationdata.urban.org/api/v1/schools/ccd/directory/2021/"
                f"?school_name={urllib.parse.quote(query)}&per_page=10"
                f"&fields=school_name,city,state_code"
            )

        req = urllib.request.Request(url, headers={'User-Agent': 'TrackLyte/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

        results = []
        seen = set()
        for school in data.get('results', []):
            if school_type == 'college':
                name = (school.get('inst_name') or '').title()
                city = (school.get('city') or '').title()
                state = school.get('state_abbr') or ''
            else:
                name = (school.get('school_name') or '').title()
                city = (school.get('city') or '').title()
                state = school.get('state_code') or ''

            if not name or name in seen:
                continue
            seen.add(name)
            display = f"{name} — {city}, {state}" if city and state else name
            results.append({'name': name, 'display': display})

        return jsonify(results)
    except Exception as e:
        print(f'School search error: {e}')
        return jsonify([])