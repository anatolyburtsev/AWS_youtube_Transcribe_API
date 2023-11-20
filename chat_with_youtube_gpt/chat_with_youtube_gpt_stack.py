import os

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_route53 as route53,
    aws_elasticloadbalancingv2 as elbv2,
    aws_certificatemanager as acm,
    CfnOutput, Duration,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2_targets as targets,
    aws_route53_targets as route53_targets,
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
            timeout=Duration.minutes(15),
            memory_size=1024,
        )

        zone_name = os.environ['ZONE_NAME']
        hosted_zone = route53.HostedZone.from_lookup(self, "HostedZone", domain_name=zone_name)
        alb_dns_name = f"youtube-transcriber.{zone_name}"

        vpc = ec2.Vpc(
            self,
            "VPC",
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="VpcSubnetGroup", subnet_type=ec2.SubnetType.PUBLIC
                )
            ],
        )

        security_group = ec2.SecurityGroup(self, "LoadBalancerSG", vpc=vpc)
        load_balancer = elbv2.ApplicationLoadBalancer(
            self,
            "LoadBalancer",
            vpc=vpc,
            internet_facing=True,
            security_group=security_group,
        )

        domainRecords = route53.ARecord(
            self,
            "DomainRecord",
            zone=hosted_zone,
            record_name=alb_dns_name,
            target=route53.RecordTarget.from_alias(
                route53_targets.LoadBalancerTarget(load_balancer)
            ),
        )

        certificate = acm.Certificate(
            self,
            "Certificate",
            domain_name=alb_dns_name,
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        listener = load_balancer.add_listener(
            "LoadBalancerListener", port=443, certificates=[certificate]
        )

        listener.add_targets(
            "LoadBalancerTargets",
            targets=[targets.LambdaTarget(transcribe_lambda)],
            health_check=elbv2.HealthCheck(enabled=False),
        )

        CfnOutput(self, "DomainRecordOutput", value=domainRecords.domain_name)
