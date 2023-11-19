from aws_cdk import (
    Stack,
    aws_lambda as lambda_,

    aws_apigateway as apigateway,
    CfnOutput, Duration
)
from constructs import Construct


class ChatWithYoutubeGptStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define the Lambda function
        transcribe_lambda = lambda_.Function(
            self, 'TranscribeHandler',
            function_name='TranscribeHandler',
            runtime=lambda_.Runtime.FROM_IMAGE,
            code=lambda_.Code.from_asset_image('lambda'),
            handler=lambda_.Handler.FROM_IMAGE,
            timeout=Duration.minutes(5)
        )

        # Define the API Gateway
        api = apigateway.RestApi(
            self, 'Endpoint',
            rest_api_name='YoutubeTranscribeAPI'
        )

        # Lambda Integration
        transcribe_integration = apigateway.LambdaIntegration(transcribe_lambda)

        # Define API Key for the POST method
        api_key = apigateway.ApiKey(
            self, 'TranscribeApiKey',
            enabled=True
        )

        # Define Usage Plan
        usage_plan = apigateway.UsagePlan(
            self, 'UsagePlan',
            name='BasicUsagePlan',
            throttle={
                'rate_limit': 10,
                'burst_limit': 2
            }
        )

        usage_plan.add_api_key(api_key)
        usage_plan.add_api_stage(
            stage=api.deployment_stage
        )

        transcribe_resource = api.root.add_resource('transcribe')
        transcribe_resource.add_method(
            'POST', transcribe_integration,
            api_key_required=True
        )

        CfnOutput(
            self, 'ApiUrl',
            value=api.url,
            description='The URL of the API Gateway'
        )

        CfnOutput(
            self, 'ApiKey',
            value=api_key.key_id,
            description='API Key Id for accessing the POST method'
        )
