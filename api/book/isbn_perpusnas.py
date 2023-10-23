import datetime
import json
import re

from flask import Blueprint, request
from flask_restx import Resource
from enum import Enum
from api import api
from helper import success_response, error_response, flask_response
from controller.book.isbn_perpusnas.search import Search

isbn_perpusnas = Blueprint("isbn_perpusnas", __name__)
ns_api = api.namespace("isbn_perpusnas", description="Book")


class TitleAuthorEnum(Enum):
    Judul = "Judul"
    Pengarang = "Pengarang"
    Penerbit = "Penerbit"
    ISBN = "ISBN"


@ns_api.route("/search", methods=["GET"])
class BookSearch(Resource):
    @api.doc(
        responses=flask_response("get"),
        params={
            "keyword": {"description": "keyword", "required": True},
            "search_by": {
                "description": "Parameter for selecting search type",
                "enum": [e.value for e in TitleAuthorEnum],
                "default": TitleAuthorEnum.Judul.value,
            },
        },
    )
    def get(self):
        try:
            keyword = request.values.get("keyword")
            search_by = request.values.get("search_by")
            search = Search()
            data = search.search(kd1=search_by, kd2=keyword, limit=1000, offset=0)
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
