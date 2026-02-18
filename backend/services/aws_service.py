import aioboto3
from botocore.exceptions import ClientError
from typing import Dict, Any, List

from config.aws_config import aws_config

class AWSService:
    """
    Service for interacting with AWS APIs.
    Adapts the logic from the aws.py prototype.
    """
    
    def __init__(self):
        # This list is taken directly from your aws.py script. It's excellent.
        self.resource_types = [
            'AWS::EC2::Instance', 'AWS::EC2::SecurityGroup', 'AWS::EC2::Volume', 'AWS::EC2::VPC',
            'AWS::EC2::Subnet', 'AWS::EC2::InternetGateway', 'AWS::EC2::NatGateway', 'AWS::EC2::RouteTable',
            'AWS::S3::Bucket', 'AWS::RDS::DBInstance', 'AWS::RDS::DBSubnetGroup', 'AWS::DynamoDB::Table',
            'AWS::Lambda::Function', 'AWS::IAM::Role', 'AWS::IAM::Policy', 'AWS::KMS::Key',
            'AWS::ElasticLoadBalancingV2::LoadBalancer', 'AWS::CloudFront::Distribution', 'AWS::Route53::HostedZone',
            'AWS::SNS::Topic', 'AWS::SQS::Queue', 'AWS::ECS::Cluster', 'AWS::ECS::Service', 'AWS::EKS::Cluster',
            'AWS::ApiGateway::RestApi', 'AWS::CloudFormation::Stack'
        ] # Using a truncated list for speed, but the full list from aws.py can be used.

    async def get_session(self):
        """Creates an async boto3 session."""
        return aioboto3.Session(
            aws_access_key_id=aws_config.aws_access_key_id,
            aws_secret_access_key=aws_config.aws_secret_access_key,
            region_name=aws_config.aws_region
        )

    async def discover_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discovers all AWS resources for the configured account and region
        using the AWS Config service.
        """
        all_resources = {}
        session = await self.get_session()
        
        async with session.client("config") as config_client:
            for rtype in self.resource_types:
                print(f"Discovering resources of type: {rtype}")
                try:
                    resources = []
                    paginator = config_client.get_paginator('list_discovered_resources')
                    
                    async for page in paginator.paginate(resourceType=rtype):
                        for resource_identifier in page.get('resourceIdentifiers', []):
                            try:
                                history = await config_client.get_resource_config_history(
                                    resourceType=rtype,
                                    resourceId=resource_identifier['resourceId'],
                                    limit=1
                                )
                                if history.get('configurationItems'):
                                    resources.append(history['configurationItems'][0])
                            except ClientError as e:
                                print(f"Warning: Could not fetch config for {resource_identifier['resourceId']}: {e}")
                    
                    all_resources[rtype] = resources
                except ClientError as e:
                    print(f"Error: Could not list resources for {rtype}: {e}")
                    all_resources[rtype] = []
        
        return all_resources

# Global instance
aws_service = AWSService()