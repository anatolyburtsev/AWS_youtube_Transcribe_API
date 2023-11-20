curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -H "Content-Type: application/json" \
-d '{
    "httpMethod": "POST",
    "path": "/transcribe",
    "headers": {
        "Content-Type": "application/json",
        "x-api-key": "XXXXXXXXXX"
    },
    "body": "{\"url\": \"https://www.youtube.com/watch?v=XGJNo8TpuVA\"}"
}'
