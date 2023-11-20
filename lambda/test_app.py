import json
from app import handler


def test_handler_success():
    event = {
        "body": json.dumps({"some": "data"})
    }
    expected_response = {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"success": "OK", "data": {"some": "data"}})
    }

    response = handler(event, None)
    assert response == expected_response, "Handler did not return expected successful response"


def test_handler_invalid_json():
    event = {
        "body": "{invalid: json,}"
    }
    expected_response = {
        "isBase64Encoded": False,
        "statusCode": 400,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": "Invalid JSON in request"})
    }

    response = handler(event, None)
    assert response == expected_response, "Handler did not handle invalid JSON as expected"
