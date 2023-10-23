import datetime
import json
import re
import io

from flask import Blueprint, request, send_file
from flask_restx import Resource
from enum import Enum
from api import api
from helper import success_response, error_response, flask_response
from controller.book.ebooksdirectory.allcategories import AllCategories
from controller.book.ebooksdirectory.getbooks import GetBooks

ebooksdirectory = Blueprint("ebooksdirectory", __name__)
ns_api = api.namespace("ebooksdirectory", description="Book")


class OptionsEnum(Enum):
    cat = "categories"
    new = "new"
    top = "top20"
    pop = "popular"


@ns_api.route("/get-allcategories", methods=["GET"])
class GetAllCategories(Resource):
    @api.doc(
        responses=flask_response("get")
    )
    def get(self):
        try:
            allcat = AllCategories()
            data = allcat.allcategories()
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


@ns_api.route("/get-books", methods=["GET"])
class TheGetBooks(Resource):
    @api.doc(
        responses=flask_response("get"),
        params={
            "option": {
                "description": "Parameters to determine the option",
                "enum": [e.value for e in OptionsEnum],
                "default": OptionsEnum.cat.value
            },
            "category": {
                "description": "id taken from get-allcategories"
            },
            "page": {
                "description": "Page number\nNOTE: for category options no page numbers are required. So these page numbers are used for options other than categories.",
                "type": int,
                "default": 1,
            }
        }
    )
    def get(self):
        try:
            option = request.values.get("option")
            category = request.values.get("category")
            page = request.values.get("page")
            gb = GetBooks()
            data = gb.getbooks(option=option, id=category, page=page)
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
