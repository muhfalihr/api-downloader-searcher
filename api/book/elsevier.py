import datetime
import json
import re
import io

from flask import Blueprint, request, send_file
from flask_restx import Resource, fields
from enum import Enum
from api import api
from helper import success_response, error_response, flask_response
from controller.book.elsevier.search import Search


elsevier = Blueprint("elsevier", __name__)
ns_api = api.namespace("elsevier", description="Book")


class SortByEnum(Enum):
    relevance = "Relevance"
    alphabeticalAZ = "Alphabetical (A-Z)"
    alphabeticalZA = "Alphabetical (Z-A)"
    datepubasc = "Date Published (asc)"
    datepubdesc = "Date Published (desc)"


@ns_api.route("/search", methods=["GET"])
class BooksSearch(Resource):
    @api.doc(
        responses=flask_response("get"),
        params={
            "keyword": {"description": "keyword", "required": True},
            "sortby": {
                "description": "Parameter for sort the result",
                "enum": [e.value for e in SortByEnum],
                "default": SortByEnum.relevance.value
            },
            "page": {
                "description": "Page number",
                "type": int,
                "default": 1,
            }
        }
    )
    def get(self):
        try:
            keyword = request.values.get("keyword")
            sortby = request.values.get("sortby")
            page = request.values.get("page")
            search = Search()
            data = search.search(keyword=keyword, page=page, sortby=sortby)
            return (
                success_response(data, message="success"), 200
            )
        except Exception as e:
            if re.search("status code", str(e)):
                pattern = r"status code (\d+) : (.+)"
                match = re.search(pattern, str(e))
                if match:
                    status_code = match.group(1)
                    message = match.group(2)
                    return error_response(
                        message=json.dumps(
                            dict(
                                message=message,
                                status=int(status_code),
                            )
                        ),
                        status=int(status_code),
                    )
                else:
                    return error_response(
                        message=json.dumps(dict(message=str(e), status=500))
                    )
            else:
                return error_response(
                    message=json.dumps(dict(message=str(e), status=500))
                )
