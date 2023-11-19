# Use a prebuilt image with Python runtime
FROM public.ecr.aws/lambda/python:3.11

# Copy the handler function
COPY app.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD ["app.handler"]
