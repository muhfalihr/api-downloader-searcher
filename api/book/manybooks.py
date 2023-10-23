import datetime
import json
import re

from flask import Blueprint, request, jsonify
from flask_restx import Resource
from enum import Enum
from api import api
from helper import success_response, error_response, flask_response
from controller.book.manybooks.search import Search

manybooks = Blueprint("manybooks", __name__)
ns_api = api.namespace("manybooks", description="Book")


class TitleAuthorEnum(Enum):
    title = "title"
    author = "author"
    popularity = "popularity"
    rating = "rating"


@ns_api.route("/search", methods=["GET"])
class BookSearch(Resource):
    @api.doc(
        responses=flask_response("get"),
        params={
            "keyword": {"description": "keyword", "required": True},
            "sort_by": {
                "description": "Parameter for sort the result",
                "enum": [e.value for e in TitleAuthorEnum],
                "default": TitleAuthorEnum.popularity.value,
            },
            "page": {"description": "page start from 0", "default": 0},
        },
    )
    def get(self):
        try:
            keyword = request.values.get("keyword")
            sort_by = request.values.get("sort_by")
            page = request.values.get("page")
            search = Search()
            data = search.search(keyword=keyword, sort_by=sort_by, page=page)
            return (
                success_response(data=data, message=f"success"),
                200,
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
