import datetime
import json
import re
import io

from flask import Blueprint, request, send_file
from flask_restx import Resource, fields
from enum import Enum
from api import api
from helper import success_response, error_response, flask_response
from controller.book.springeropen.search import Search
from controller.book.springeropen.downloader import Downloader


springeropen = Blueprint("springeropen", __name__)
ns_api = api.namespace("springeropen", description="Book")


class SortByEnum(Enum):
    relevance = "Relevance"
    date = "PubDate"


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
            data = search.search(keyword=keyword, sortby=sortby, page=page)
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
            "url": {
                "description": "slug",
                "required": True
            }
        },
        description="URL taken from search results."
    )
    def get(self):
        try:
            url = request.values.get("url")
            downloader = Downloader()
            data, filename, content_type = downloader.download(url=url)
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
