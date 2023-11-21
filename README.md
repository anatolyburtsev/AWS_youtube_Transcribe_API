

OpenAPI schema:
```json

{
  "openapi": "3.1.0",
  "info": {
    "title": "YouTube Transcriber API",
    "description": "API for transcribing YouTube videos.",
    "version": "v1.0.0"
  },
  "servers": [
    {
      "url": "https://FILL_ME"
    }
  ],
  "paths": {
    "/transcribe": {
      "post": {
        "description": "Transcribes the audio from a given YouTube video URL.",
        "operationId": "TranscribeVideo",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "url": {
                    "type": "string",
                    "example": "https://www.youtube.com/watch?v=XGJNo8TpuVA"
                  }
                },
                "required": ["url"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Transcription result",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "transcription": {
                      "type": "string",
                      "example": "Sample transcription text here."
                    }
                  }
                }
              }
            }
          },
          "400": {
            "description": "Invalid request"
          },
          "401": {
            "description": "Unauthorized - API key missing or invalid"
          },
          "500": {
            "description": "Internal server error"
          }
        },
        "security": [
          {
            "api_key": []
          }
        ],
        "deprecated": false
      }
    }
  },
  "components": {
    "securitySchemes": {
      "api_key": {
        "type": "apiKey",
        "name": "x-api-key",
        "in": "header"
      }
    }
  }
}
```