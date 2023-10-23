import datetime
import json
import re
import io

from flask import Blueprint, request, send_file
from flask_restx import Resource, fields
from enum import Enum
from api import api
from helper import success_response, error_response, flask_response
from controller.book.pdfdrive.search import Search
from controller.book.pdfdrive.categories import Categories


pdfdrive = Blueprint("pdfdrive", __name__)
ns_api = api.namespace("pdfdrive", description="Book")


class PageCountEnum(Enum):
    anypages = "Any Pages"
    satu = "1-24"
    dua = "25-50"
    tiga = "51-100"
    empat = "100+"


class PubYearEnum(Enum):
    pubyear = "Pub. Year"
    aftr2015 = "After 2015"
    aftr2010 = "After 2010"
    aftr2005 = "After 2005"
    aftr2000 = "After 2000"
    aftr1990 = "After 1990"


@ns_api.route("/search", methods=["GET"])
class BookSearch(Resource):
    @api.doc(
        responses=flask_response("get"),
        params={
            "keyword": {"description": "keyword", "required": True},
            "pagecount": {
                "description": "number of books on one page",
                "enum": [e.value for e in PageCountEnum],
                "default": PageCountEnum.anypages.value
            },
            "pubyear": {
                "description": "the year the book was published",
                "enum": [e.value for e in PubYearEnum],
                "default": PubYearEnum.pubyear.value
            },
            "exact_match": {
                "description": "select true if you want to use an exact match select false if not",
                "type": bool,
                "in": "query",
                "default": False
            },
            "page": {
                "description": "Page number",
                "type": int,
                "default": 1,
            },
        }
    )
    def get(self):
        try:
            keyword = request.values.get("keyword")
            pagecount = request.values.get("pagecount")
            pubyear = request.values.get("pubyear")
            em = request.values.get("exact_match")
            page = request.values.get("page")
            search = Search()
            data = search.search(
                keyword=keyword, pagecount=pagecount, em=em, page=page, pub_year=pubyear)
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


@ns_api.route("/books-categories", methods=["GET"])
class BooksCategories(Resource):
    @api.doc(
        responses=flask_response("get"),
        description="Returns All Categories"
    )
    def get(self):
        try:
            allcat = Categories()
            data = allcat.categories()
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


@ns_api.route("/books-by-category", methods=["GET"])
class BooksByCat(Resource):
    @api.doc(
        responses=flask_response("get"),
        params={
            "id": {
                "description": "determine the id from the books-categories results",
                "required": True
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
            id = request.values.get("id")
            page = request.values.get("page")
            bookcat = Search()
            data = bookcat.search(iscategory=True, idcat=id, page=page)
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
