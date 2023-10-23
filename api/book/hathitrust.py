import datetime
import json
import re
import io

from flask import Blueprint, request, send_file
from flask_restx import Resource
from enum import Enum
from api import api
from helper import success_response, error_response, flask_response
from controller.book.hathitrust.search import Search

hathitrust = Blueprint("hathitrust", __name__)
ns_api = api.namespace("hathitrust", description="Book")


class CategoriesEnum(Enum):
    ftaf = "full_text_and_all_fields"
    all = "all"
    title = "title"
    author = "author"
    subject = "subject"
    isn = "isn"
    publisher = "publisher"
    seriestitle = "seriestitle"


@ns_api.route("/search", methods=["GET"])
class BookSearch(Resource):
    @api.doc(
        responses=flask_response("get"),
        params={
            "keyword": {"description": "keyword", "required": True},
            "category": {
                "description": "Parameters to determine the category",
                "enum": [e.value for e in CategoriesEnum],
                "default": CategoriesEnum.all.value
            },
            "page": {
                "description": "Page number",
                "type": int,
                "default": 1,
            },
            "pagesize": {
                "description": "The number of books on one page",
                "type": int,
                "default": 10
            }
        },
    )
    def get(self):
        try:
            keyword = request.values.get("keyword")
            category = request.values.get("category")
            page = request.values.get("page")
            pagesize = request.values.get("pagesize")
            search = Search()
            data = search.search(
                keyword=keyword, category=category, page=page, pagesize=pagesize)
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
