import datetime
import json
import re
import io

from flask import Blueprint, request, send_file
from flask_restx import Resource
from enum import Enum
from api import api
from helper import success_response, error_response, flask_response
from controller.book.freetechbooks.all import All

freetechbooks = Blueprint("freetechbooks", __name__)
ns_api = api.namespace("freetechbooks", description="Book")


class OptionsEnum(Enum):
    all = "topics"
    categories = "categories"
    authors = "authors"
    publishers = "publishers"
    licenses = "licenses"


@ns_api.route("/get-all-books-by", methods=["GET"])
class GetAllBooksBy(Resource):
    @api.doc(
        responses=flask_response("get"),
        params={
            "option": {
                "description": "Parameters to determine the option\nNOTE: \"topics\" option is an option that contains all books without filtering.",
                "enum": [e.value for e in OptionsEnum],
                "default": OptionsEnum.all.value
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
            page = request.values.get("page")
            all = All()
            data = all.all(option=option, page=page)
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


@ns_api.route("/get-books-by-id", methods=["GET"])
class GetBooksByID(Resource):
    @api.doc(
        responses=flask_response("get"),
        params={
            "id": {
                "description": "using the result id from onpoint get-all-books-by"
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
            id = request.values.get("id")
            page = request.values.get("page")
            all = All()
            data = all.all(datascrawl=True, idlink=id, page=page)
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
