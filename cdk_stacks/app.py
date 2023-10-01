#!/usr/bin/env python3
import os

import aws_cdk as cdk

from rag_with_aos import (
  VpcStack,
  BastionHostEC2InstanceStack,
  OpenSearchStack,
  SageMakerStudioStack,
  SageMakerLambdaLayerStack,
  JumpStartModelDeployLambdaStack,
  SageMakerEndpointIAMRoleStack,
  CustomResourceStack
)

APP_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, 'RAGHaystackVpcStack',
  env=APP_ENV)

ops_stack = OpenSearchStack(app, 'RAGHaystackOpenSearchStack',
  vpc_stack.vpc,
  env=APP_ENV
)
ops_stack.add_dependency(vpc_stack)

bastion_host = BastionHostEC2InstanceStack(app, 'RAGHaystackBastionHost',
  vpc_stack.vpc,
  ops_stack.ops_client_sg,
  env=APP_ENV
)
bastion_host.add_dependency(ops_stack)

sm_studio_stack = SageMakerStudioStack(app, 'RAGHaystackSageMakerStudioStack',
  vpc_stack.vpc,
  ops_stack.ops_client_sg.security_group_id,
  env=APP_ENV
)
sm_studio_stack.add_dependency(bastion_host)

lambda_layer_stack = SageMakerLambdaLayerStack(app, "RAGHaystackSMPySDKLambdaLayerStack",
  env=APP_ENV)
lambda_layer_stack.add_dependency(sm_studio_stack)

sagemaker_endpoint_iam_role_stack = SageMakerEndpointIAMRoleStack(app, "RAGHaystackSMEndpointRoleStack",
  env=APP_ENV)
sagemaker_endpoint_iam_role_stack.add_dependency(lambda_layer_stack)

lambda_function_stack = JumpStartModelDeployLambdaStack(app, "RAGHaystackSMJSModelDeployLambdaStack",
  lambda_layer_stack.lambda_layer,
  sagemaker_endpoint_iam_role_arn=sagemaker_endpoint_iam_role_stack.sagemaker_endpoint_role_arn,
  env=APP_ENV)
lambda_function_stack.add_dependency(sagemaker_endpoint_iam_role_stack)

custom_resource_stack = CustomResourceStack(app, "RAGHaystackSMJSModelEndpointStack",
  lambda_function_stack.lambda_function_arn,
  env=APP_ENV)
custom_resource_stack.add_dependency(lambda_function_stack)

app.synth()
