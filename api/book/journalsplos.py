import datetime
import json
import re
import io

from flask import Blueprint, request, send_file
from flask_restx import Resource
from enum import Enum
from api import api
from helper import success_response, error_response, flask_response
from controller.book.journalsplos.search import Search
from controller.book.journalsplos.downloader import Downloader

journalsplos = Blueprint("journalsplos", __name__)
ns_api = api.namespace("journalsplos", description="Book")


class SortByEnum(Enum):
    relevance = "RELEVANCE"
    dnf = "DATE_NEWEST_FIRST"
    dof = "DATE_OLDEST_FIRST"
    mvd = "MOST_VIEWS_30_DAYS"
    mvat = "MOST_VIEWS_ALL_TIME"
    mc = "MOST_CITED"


class CategorysEnum(Enum):
    All_Fields = "everything"
    Title = "title"
    Author = "author"
    Body = "body"
    Abstract = "abstract"
    Subject = "subject"
    Publication_Date = "publication_date"


@ns_api.route("/search", methods=["GET"])
class ArticleSearch(Resource):
    @api.doc(
        responses=flask_response("get"),
        params={
            "keyword": {"description": "keyword", "required": True},
            "category": {
                "description": "Parameters to determine the category",
                "enum": [e.value for e in CategorysEnum],
                "default": CategorysEnum.All_Fields.value,
            },
            "pubdate_start": {
                "description": "Determine the Pubdate filter starting from what date\nExample: 2023-01-01"
            },
            "pubdate_end": {
                "description": "Determine which date the pubdate filter ends\nExample: 2023-01-01"
            },
            "page_size": {
                "description": "The number of articles on one page",
                "enum": [15, 30, 60],
                "default": 15
            },
            "sort_by": {
                "description": "Parameter for sort the result",
                "enum": [e.value for e in SortByEnum],
                "default": SortByEnum.relevance.value,
            },
            "page": {"description": "page start from 1", "default": 1}
        },
    )
    def get(self):
        try:
            keyword = request.values.get("keyword")
            category = request.values.get("category")
            start = request.values.get("pubdate_start") if not "" else None
            end = request.values.get("pubdate_end") if not "" else None
            pagesize = request.values.get("page_size")
            sortby = request.values.get("sort_by")
            page = request.values.get("page")
            search = Search()
            data = search.search(keyword=keyword, category=category, filterstartdate=start,
                                 filterenddate=end, sizepage=pagesize, sortby=sortby, page=page)
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
                "required": True,
                "example": "https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0280108&type=printable",
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
