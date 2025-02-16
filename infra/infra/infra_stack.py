from aws_cdk import (
    aws_certificatemanager as acm,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_ecs as ecs,
    aws_elasticache as elasticache,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    aws_logs as logs,
    aws_rds as rds,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_secretsmanager as secretsmanager,
    Duration,
    RemovalPolicy,
    Stack, CfnOutput
)
from constructs import Construct

DOMAIN_NAME="beatblend.ch"


class InfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define your VPC
        vpc = ec2.Vpc(
            self,
            "VPC",
            max_azs=2
        )

        # Create an ECS Cluster
        cluster = ecs.Cluster(
            self,
            "EcsCluster",
            vpc=vpc
        )

        # Obtain SSL/TLS Certificate
        hosted_zone = route53.HostedZone.from_lookup(
            self,
            "HostedZone",
            domain_name=DOMAIN_NAME
        )

        certificate = acm.Certificate(
            self,
            "Certificate",
            domain_name=DOMAIN_NAME,
            subject_alternative_names=["www." + DOMAIN_NAME, "api." + DOMAIN_NAME],
            validation=acm.CertificateValidation.from_dns(hosted_zone)
        )

        # Task Role (for your application inside the container)
        task_role = iam.Role(
            self,
            "TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )

        # Execution Role (for ECS tasks to interact with AWS services)
        execution_role = iam.Role(
            self,
            "ExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )

        # Attach the AWS managed policy for ECS task execution
        execution_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
        )

        # Create a Fargate Task Definition for the frontend
        frontend_task_definition = ecs.FargateTaskDefinition(
            self,
            "FrontendTaskDef",
            memory_limit_mib=512,
            cpu=256,
            execution_role=execution_role,
            task_role=task_role,
        )

        # Create a Fargate Task Definition for the backend
        backend_task_definition = ecs.FargateTaskDefinition(
            self,
            "BackendTaskDef",
            memory_limit_mib=512,
            cpu=256,
            execution_role=execution_role,
            task_role=task_role,
        )

        # ALB Security Group
        alb_sg = ec2.SecurityGroup(
            self,
            "ALBSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for the ALB"
        )

        # Ingress rule for HTTP (port 80)
        alb_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow inbound HTTP traffic from anywhere"
        )

        # Ingress rule for HTTPS (port 443)
        alb_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(443),
            "Allow inbound HTTPS traffic from anywhere"
        )

        # Security Group for Frontend Service
        frontend_sg = ec2.SecurityGroup(
            self,
            "FrontendSG",
            vpc=vpc,
            allow_all_outbound=True,
            description="Allow HTTP traffic from ALB"
        )

        # Allow inbound traffic from ALB
        frontend_sg.add_ingress_rule(
            ec2.Peer.security_group_id(alb_sg.security_group_id),
            ec2.Port.tcp(80),
            "Allow HTTP traffic from ALB"
        )

        # Security Group for Backend Service
        backend_sg = ec2.SecurityGroup(
            self,
            "BackendSG",
            vpc=vpc,
            allow_all_outbound=True,
            description="Allow traffic from Frontend Service"
        )

        # Allow inbound traffic from ALB to Backend Service
        backend_sg.add_ingress_rule(
            ec2.Peer.security_group_id(alb_sg.security_group_id),
            ec2.Port.tcp(8000),
            "Allow HTTP traffic from ALB"
        )

        # Security Group for Postgres Instance
        postgres_sg = ec2.SecurityGroup(
            self,
            "PostgresSG",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for the Postgres Database"
        )

        # Allow inbound traffic from Backend Security Group on port 5432
        postgres_sg.add_ingress_rule(
            ec2.Peer.security_group_id(backend_sg.security_group_id),
            ec2.Port.tcp(5432),
            "Allow PostgreSQL access from Backend Service"
        )

        # Security Group for Redis
        redis_sg = ec2.SecurityGroup(
            self,
            "RedisSG",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for Redis"
        )

        # Allow inbound traffic from Backend Security Group on Redis port (6379)
        redis_sg.add_ingress_rule(
            ec2.Peer.security_group_id(backend_sg.security_group_id),
            ec2.Port.tcp(6379),
            "Allow Redis access from Backend Service"
        )

        # Subnets for ALB & ECS Services
        alb_subnets = ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
        vpc_subnets = ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)

        # Use the existing vpc_subnets to select subnets
        private_subnets = vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS).subnets

        # Create a subnet group for ElastiCache
        redis_subnet_group = elasticache.CfnSubnetGroup(
            self,
            "RedisSubnetGroup",
            description="Subnet group for Redis",
            subnet_ids=[subnet.subnet_id for subnet in private_subnets],
            cache_subnet_group_name="redis-subnet-group"
        )

        # Create an Application Load Balancer (ALB)
        alb = elbv2.ApplicationLoadBalancer(
            self,
            "ALB",
            vpc=vpc,
            internet_facing=True,
            security_group=alb_sg,
            vpc_subnets=alb_subnets
        )

        # Redirect HTTP to HTTPS
        alb.add_listener(
            "HTTPListener",
            port=80,
            default_action=elbv2.ListenerAction.redirect(
                protocol="HTTPS",
                port="443",
                permanent=True
            ),
            open=True
        )

        # Point domain to the ALB
        route53.ARecord(
            self,
            "RootDomainAliasRecord",
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(targets.LoadBalancerTarget(alb)),
            record_name=DOMAIN_NAME,
        )

        route53.ARecord(
            self,
            "WWWSubdomainAliasRecord",
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(targets.LoadBalancerTarget(alb)),
            record_name="www." + DOMAIN_NAME,
        )

        # Point api.beatblend.ch to the ALB
        route53.ARecord(
            self,
            "APISubdomainAliasRecord",
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(targets.LoadBalancerTarget(alb)),
            record_name="api." + DOMAIN_NAME,
        )

        # Redis Replication Group
        redis_cluster = elasticache.CfnReplicationGroup(
            self,
            "RedisCluster",
            replication_group_description="Redis replication group for BeatBlend",
            engine="redis",
            cache_node_type="cache.t3.small",
            engine_version="6.x",
            automatic_failover_enabled=False, # set to False due to num_cache_clusters
            cache_subnet_group_name=redis_subnet_group.cache_subnet_group_name,
            security_group_ids=[redis_sg.security_group_id],
            num_cache_clusters=1,  # Adjust based on your needs
            multi_az_enabled=False,
            transit_encryption_enabled=True,  # Enable in-transit encryption
            at_rest_encryption_enabled=True,  # Enable at-rest encryption
            # kms_key_id="alias/aws/elasticache",  # Use default AWS managed key # removed due to issues
            # Optional: Specify parameter group
            # cache_parameter_group_name=redis_parameter_group.ref,
        )

        redis_cluster.add_dependency(redis_subnet_group)

        # Create a PostgreSQL RDS instance
        postgres = rds.DatabaseInstance(
            self,
            "PostgresDB",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16_3
            ),
            vpc=vpc,
            vpc_subnets=vpc_subnets,
            security_groups=[postgres_sg],
            multi_az=False,
            allocated_storage=100,
            # max_allocated_storage=150,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.SMALL
            ),
            database_name="songs",
            credentials=rds.Credentials.from_generated_secret("postgres"),
            removal_policy=RemovalPolicy.DESTROY,  # Be cautious with this in production
            deletion_protection=False,  # Be cautious with this in production
        )

        # Grant read access to the secret for the execution role
        postgres.secret.grant_read(execution_role)

        # Retrieve the secret by name
        spotify_secrets = secretsmanager.Secret.from_secret_name_v2(
            self,
            "SpotifySecrets",
            secret_name="SpotifySecrets"
        )

        jwt_secrets = secretsmanager.Secret.from_secret_name_v2(
            self,
            "JWTSecrets",
            secret_name="JWTSecrets"
        )

        discogs_secrets = secretsmanager.Secret.from_secret_name_v2(
            self,
            "DiscogsSecrets",
            secret_name="DiscogsSecrets"
        )

        spotify_secrets.grant_read(execution_role)
        jwt_secrets.grant_read(execution_role)
        discogs_secrets.grant_read(execution_role)

        # Add container to the task definition
        backend_container = backend_task_definition.add_container(
            "BackendContainer",
            container_name="BackendContainer",
            image=ecs.ContainerImage.from_ecr_repository(
                ecr.Repository.from_repository_name(self, "BackendRepo", "beatblend-server"),
                tag="latest"
            ),
            logging=ecs.LogDriver.aws_logs(stream_prefix="Backend", log_retention=logs.RetentionDays.ONE_WEEK),
            environment={
                "SPOTIFY_CLIENT_ID": "d3d3c0137d7942c893be8c1157ed65fb",
                "SPOTIFY_REDIRECT_URI": f"https://{DOMAIN_NAME}/spotify-callback",
                "JWT_ALGORITHM": "HS256",
                "JWT_EXPIRE_MINUTES": "60",
                "POSTGRES_DB": "songs",
                "POSTGRES_HOST": postgres.db_instance_endpoint_address,
                "POSTGRES_PORT": postgres.db_instance_endpoint_port,
                "DISCOGS_API_URL": "https://api.discogs.com/database/search",
                "REDIS_HOST": redis_cluster.attr_primary_end_point_address,
                "REDIS_PORT": redis_cluster.attr_primary_end_point_port,
                "REDIS_SSL": "true",  # Since transit encryption is enabled
                "BASE_URL": DOMAIN_NAME,
            },
            secrets={
                "SPOTIFY_CLIENT_SECRET": ecs.Secret.from_secrets_manager(spotify_secrets, "SPOTIFY_CLIENT_SECRET"),
                "JWT_SECRET_KEY": ecs.Secret.from_secrets_manager(jwt_secrets, "JWT_SECRET_KEY"),
                "POSTGRES_USER": ecs.Secret.from_secrets_manager(postgres.secret, "username"),
                "POSTGRES_PASSWORD": ecs.Secret.from_secrets_manager(postgres.secret, "password"),
                "DISCOGS_API_TOKEN": ecs.Secret.from_secrets_manager(discogs_secrets, "DISCOGS_API_TOKEN"),
            }
        )

        # Map container port to host
        backend_container.add_port_mappings(
            ecs.PortMapping(container_port=8000, protocol=ecs.Protocol.TCP)
        )

        # Add container to the task definition
        frontend_container = frontend_task_definition.add_container(
            "FrontendContainer",
            container_name="FrontendContainer",
            image=ecs.ContainerImage.from_ecr_repository(
                ecr.Repository.from_repository_name(self, "FrontendRepo", "beatblend-client"),
                tag="latest"
            ),
            logging=ecs.LogDriver.aws_logs(stream_prefix="Frontend", log_retention=logs.RetentionDays.ONE_WEEK),
        )

        # Map container port to host
        frontend_container.add_port_mappings(
            ecs.PortMapping(container_port=80, protocol=ecs.Protocol.TCP)
        )

        # Create the Frontend Service
        frontend_service = ecs.FargateService(
            self,
            "FrontendService",
            cluster=cluster,
            task_definition=frontend_task_definition,
            desired_count=1,
            security_groups=[frontend_sg],
            assign_public_ip=False, # Use private subnets
            vpc_subnets=vpc_subnets
        )

        # Create the Backend Service
        backend_service = ecs.FargateService(
            self,
            "BackendService",
            cluster=cluster,
            task_definition=backend_task_definition,
            desired_count=1,
            security_groups=[backend_sg],
            assign_public_ip=False, # Use private subnets
            vpc_subnets=vpc_subnets
        )

        frontend_target_group = elbv2.ApplicationTargetGroup(
            self,
            "FrontendTG",
            vpc=vpc,
            protocol=elbv2.ApplicationProtocol.HTTP,
            port=80,
            targets=[frontend_service.load_balancer_target(
                container_name="FrontendContainer",
                container_port=80
            )],
            health_check=elbv2.HealthCheck(
                path="/",
                interval=Duration.seconds(30),
                healthy_threshold_count=2,
                unhealthy_threshold_count=5,
                timeout=Duration.seconds(5),
            )
        )

        backend_target_group = elbv2.ApplicationTargetGroup(
            self,
            "BackendTG",
            vpc=vpc,
            protocol=elbv2.ApplicationProtocol.HTTP,
            port=8000,
            targets=[backend_service.load_balancer_target(
                container_name="BackendContainer",
                container_port=8000
            )],
            health_check=elbv2.HealthCheck(
                path="/health",  # Adjust the path according to your backend health endpoint
                interval=Duration.seconds(30),
                healthy_threshold_count=2,
                unhealthy_threshold_count=5,
                timeout=Duration.seconds(5),
            )
        )

        # Set up HTTPS Listener
        https_listener = alb.add_listener(
            "HTTPSListener",
            port=443,
            certificates=[certificate],
            default_action=elbv2.ListenerAction.forward([frontend_target_group]),
            open=True
        )

        https_listener.add_action(
            "BackendAction",
            priority=10,
            conditions=[
                elbv2.ListenerCondition.host_headers(["api." + DOMAIN_NAME])
            ],
            action=elbv2.ListenerAction.forward([backend_target_group])
        )

        https_listener.add_action(
            "FrontendAction",
            priority=20,
            conditions=[
                elbv2.ListenerCondition.host_headers([DOMAIN_NAME, "www." + DOMAIN_NAME])
            ],
            action=elbv2.ListenerAction.forward([frontend_target_group])
        )

        # Outputs for RDS Endpoint and Database Name
        CfnOutput(
            self,
            "DBEndpoint",
            value=postgres.db_instance_endpoint_address,
            description="Endpoint address of the RDS instance"
        )

        CfnOutput(
            self,
            "DBSecretArn",
            value=postgres.secret.secret_arn,
            description="Secret ARN for RDS credentials"
        )

        CfnOutput(
            self,
            "RedisEndpoint",
            value=redis_cluster.attr_primary_end_point_address,
            description="Primary endpoint address of the Redis cluster"
        )