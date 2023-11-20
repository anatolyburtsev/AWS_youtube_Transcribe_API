import re
from enum import Enum

from pymonad.either import Left, Right


class EarlyExitReasons(Enum):
    INVALID_JSON = 1
    INVALID_INPUT = 2
    INTERNAL_SERVER_ERROR = 3
    HEALTH_CHECK = 4
    OPTION_PRE_FLIGHT = 5
    NOT_FOUND = 6

def validate_method_and_path(event):
    match event.get("httpMethod"), event.get("path"):
        case "GET", "/":
            return Left(EarlyExitReasons.HEALTH_CHECK)
        case "OPTIONS", _:
            return Left(EarlyExitReasons.OPTION_PRE_FLIGHT)
        case "POST", "/transcribe":
            return Right(event)
        case _:
            return Left(EarlyExitReasons.NOT_FOUND)


def validate_url_body_param(body):
    youtube_url = body.get('url')
    if not youtube_url or not re.match(r"^https://www.youtube.com/watch\?v=[a-zA-Z0-9_-]*$", youtube_url):
        return Left(EarlyExitReasons.INVALID_INPUT)
    return Right(youtube_url)
