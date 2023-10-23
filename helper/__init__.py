import random
import re
from datetime import datetime, date
from decimal import Decimal
from flask import Response

from requests.cookies import RequestsCookieJar, create_cookie
import json



def json_build(data):
    if isinstance(data, dict):
        for k, v in data.items():
            data[k] = json_build(v)
    if isinstance(data, list):
        for i, v in enumerate(data):
            data[i] = json_build(v)
    if isinstance(data, tuple):
        data = json_build(list(data))
    if isinstance(data, datetime):
        data = str(data)
    if isinstance(data, date):
        data = str(data)
    if isinstance(data, Decimal):
        data = str(data)
    if data is None:
        data = ""
    return data


def response(message=None, status=None, data=None):
    return json_build(
        dict(message=str(message) if message else message, status=status, data=data)
    )


def success_response(data=None, message=None):
    return response(message, 200, data)


def error_response(message, status=500):
    return Response(message, status=status, mimetype="application/json")


def flask_response(_type):
    _type = _type.lower()
    if _type == "login":
        return {200: "OK", 500: "Authentication Failed"}
    else:
        return {200: "OK", 500: str("Could not {} data".format(_type)).title()}
