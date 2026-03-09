"""
GET /api/prices
সোনা ও রুপার সব দাম
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from _scraper import fetch_bajus


def handler(request, response):
    # CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    response.headers["Cache-Control"] = "public, s-maxage=3600, stale-while-revalidate=7200"

    if request.method == "OPTIONS":
        response.status_code = 204
        return response

    try:
        data = fetch_bajus()
        response.status_code = 200
        response.body = json.dumps(data, ensure_ascii=False, indent=2)
    except RuntimeError as e:
        response.status_code = 502
        response.body = json.dumps({"error": str(e)}, ensure_ascii=False)

    return response
