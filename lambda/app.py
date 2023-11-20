import json
import logging
from enum import Enum

from pymonad.either import Right, Left

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class EarlyExitReasons(Enum):
    INVALID_JSON = 1
    INTERNAL_SERVER_ERROR = 2


def handler(event, context):
    result = (
        Right(event)
        .then(parse_body)
        .either(
            process_early_exit,
            process_success
        )
    )

    return result


def parse_body(event):
    try:
        body = json.loads(event.get("body", '{}'))
        return Right(body)
    except json.JSONDecodeError:
        return Left(EarlyExitReasons.INVALID_JSON)


def process_early_exit(reason):
    match reason:
        case EarlyExitReasons.INVALID_JSON:
            response = {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid JSON in request"})
            }
        case EarlyExitReasons.INTERNAL_SERVER_ERROR:
            response = {
                "statusCode": 500,
                "body": json.dumps({"message": "Internal server error"})
            }
        case _:
            response = {
                "statusCode": 500,
                "body": json.dumps({"message": "Unknown error"})
            }

    return {
        "isBase64Encoded": False,
        "headers": {"Content-Type": "application/json"},
        **response
    }


def process_success(data):
    logger.info("Processing success with data: %s", data)
    # Process the data as needed
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"success": "OK", "data": data})
    }