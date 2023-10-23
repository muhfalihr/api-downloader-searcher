import datetime
import json
import re
import io

from flask import Blueprint, request, send_file
from flask_restx import Resource
from enum import Enum
from api import api
from helper import success_response, error_response, flask_response
from controller.book.gutenberg.search import Search
from controller.book.gutenberg.downloader import Downloader

gutenberg = Blueprint("gutenberg", __name__)
ns_api = api.namespace("gutenberg", description="Book")


class TitleAuthorEnum(Enum):
    all = "all"
    author = "author"
    title = "title"
    subject = "subject"


@ns_api.route("/search", methods=["GET"])
class BookSearch(Resource):
    @api.doc(
        responses=flask_response("get"),
        params={
            "keyword": {"description": "keyword", "required": True},
            "search_by": {
                "description": "Parameter for selecting search type",
                "enum": [e.value for e in TitleAuthorEnum],
                "default": TitleAuthorEnum.all.value,
            },
            "start_index": {
                "description": "get the data from which data_index, start from 1",
                "default": 1,
            },
        },
    )
    def get(self):
        try:
            keyword = request.values.get("keyword")
            search_by = request.values.get("search_by")
            start_index = request.values.get("start_index")
            search = Search()
            data = search.search(
                keyword=keyword, search_by=search_by, start_index=start_index
            )
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


@ns_api.route("/download", methods=["GET"])
class Download(Resource):
    @api.doc(
        responses=flask_response("get"),
        params={
            "url": {
                "description": "slug",
                "required": True,
                "example": "https://www.gutenberg.org/files/19312/19312-pdf.pdf",
            }
        },
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
                download_name=filename,
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
