import datetime
import json
import re
import io

from flask import Blueprint, request, send_file
from flask_restx import Resource, fields
from enum import Enum
from api import api
from helper import success_response, error_response, flask_response
from controller.book.wikibooks.action import Search, FeaturedBooks, DepartementEnum
from controller.book.wikibooks.downloader import Downloader


wikibooks = Blueprint("wikibooks", __name__)
ns_api = api.namespace("wikibooks", description="Book")


class LimitEnum(Enum):
    satu = 20
    dua = 50
    tiga = 100
    empat = 250
    lima = 500


DPE = DepartementEnum()
DEP = DPE.departementenum()


@ns_api.route("/search", methods=["GET"])
class BooksSearch(Resource):
    @api.doc(
        responses=flask_response("get"),
        params={
            "keyword": {"description": "keyword", "required": True},
            "pagesize": {
                "description": "The number of books on one page",
                "enum": [e.value for e in LimitEnum],
                "type": int,
                "default": 20
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
            pagesize = request.values.get("pagesize")
            page = request.values.get("page")
            search = Search()
            data = search.search(keyword=keyword, page=page, limit=pagesize)
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


@ns_api.route("/featured-books", methods=["GET"])
class FB(Resource):
    @api.doc(
        responses=flask_response("get"),
        params={
            "departement": {
                "description": "determine the book department",
                "enum": [e for e in DEP],
                "required": True
            }
        }
    )
    def get(self):
        try:
            departement = request.values.get("departement")
            fb = FeaturedBooks()
            data = fb.featuredbooks(departement=departement)
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


@ns_api.route("/download", methods=["GET"])
class Download(Resource):
    @api.doc(
        responses=flask_response("get"),
        params={
            "id": {
                "description": "id from search or featured-books",
                "required": True
            }
        },
        description="If the ID contains the character / then take the ID before the sign."
    )
    def get(self):
        try:
            id = request.values.get("id")
            downloader = Downloader()
            data, filename, content_type = downloader.download(id=id)
            file_stream = io.BytesIO(data)
            return send_file(
                file_stream,
                as_attachment=True,
                mimetype=content_type,
                download_name=filename
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
