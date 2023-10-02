
# RAG Application CDK Python project!

![rag_with_opensearch_arch](./rag_with_opensearch_arch.svg)

This is an QA application with LLMs and RAG project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
(.venv) $ pip install -r requirements.txt
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

### Upload Lambda Layer code

Before deployment, you should uplad zipped code files to s3 like this example:

> :warning: **Important**: Replace `lambda-layer-resources` with your s3 bucket name for lambda layer zipped code.
> :warning: To create a bucket outside of the `us-east-1` region, `aws s3api create-bucket` command requires the appropriate **LocationConstraint** to be specified in order to create the bucket in the desired region. For more information, see these [examples](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/s3api/create-bucket.html#examples).

> :warning: Make sure you have **Docker** installed.

<pre>
(.venv) $ aws s3api create-bucket --bucket lambda-layer-resources --region <i>us-east-1</i>
(.venv) $ cat <<EOF>requirements-lambda_layer.txt
 > sagemaker==2.188
 > cfnresponse==1.1.2
 > urllib3==1.26.16
 > EOF
(.venv) $ docker run -v "$PWD":/var/task "public.ecr.aws/sam/build-python3.10" /bin/sh -c "pip install -r requirements-lambda_layer.txt -t python/lib/python3.10/site-packages/; exit"
(.venv) $ zip -r sagemaker-python-sdk-lib.zip python > /dev/null
(.venv) $ aws s3 cp sagemaker-python-sdk-lib.zip s3://lambda-layer-resources/pylambda-layer/
</pre>

For more information about how to create a package for Amazon Lambda Layer, see [here](https://aws.amazon.com/premiumsupport/knowledge-center/lambda-layer-simulated-docker/).

### Deploy

Before synthesizing the CloudFormation, you should set approperly the cdk context configuration file, `cdk.context.json`.

For example:

```
{
  "opensearch_domain_name": "llm-rag-vectordb",
  "sagemaker_domain_name": "rag-workshop-studio-in-vpc",
  "lambda_layer_lib_s3_path": "s3://lambda-layer-resources/pylambda-layer/sagemaker-python-sdk-lib.zip",
  "sagemaker_jumpstart_model_info": {
    "model_id": "meta-textgeneration-llama-2-7b",
    "endpoint_name": "llama-2-7b"
  }
}
```

Now this point you can now synthesize the CloudFormation template for this code.

```
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=us-east-1 # your-aws-account-region
(.venv) $ cdk synth --all
```

Now we will be able to deploy all the CDK stacks at once like this:

```
(.venv) $ cdk deploy --require-approval never --all
```

Or, we can provision each CDK stack one at a time like this:

#### Step 1: List all CDK Stacks

```
(.venv) $ cdk list
RAGHaystackVpcStack
RAGHaystackOpenSearchStack
RAGHaystackBastionHost
RAGHaystackSageMakerStudioStack
RAGHaystackSMPySDKLambdaLayerStack
RAGHaystackSMEndpointRoleStack
RAGHaystackSMJSModelDeployLambdaStack
RAGHaystackSMJSModelEndpointStack
```

#### Step 2: Create OpenSearch cluster

```
(.venv) $ cdk deploy --require-approval never RAGHaystackVpcStack \
                                              RAGHaystackOpenSearchStack \
                                              RAGHaystackBastionHost
```

#### Step 3: Create SageMaker Studio

```
(.venv) $ cdk deploy --require-approval never RAGHaystackSageMakerStudioStack
```

#### Step 4: Deploy Text Generation LLM Endpoint

```
(.venv) $ cdk deploy --require-approval never RAGHaystackSMPySDKLambdaLayerStack \
                                              RAGHaystackSMEndpointRoleStack \
                                              RAGHaystackSMJSModelDeployLambdaStack \
                                              RAGHaystackSMJSModelEndpointStack
```

**Once all CDK stacks have been successfully created, proceed with the remaining steps of the [overall workflow](../README.md#overall-workflow).**


## Clean Up

Delete the CloudFormation stacks by running the below command.

```
(.venv) $ cdk destroy --all
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## References

  * [Build a powerful question answering bot with Amazon SageMaker, Amazon OpenSearch Service, Streamlit, and LangChain (2023-05-25)](https://aws.amazon.com/blogs/machine-learning/build-a-powerful-question-answering-bot-with-amazon-sagemaker-amazon-opensearch-service-streamlit-and-langchain/)
  * [Use proprietary foundation models from Amazon SageMaker JumpStart in Amazon SageMaker Studio (2023-06-27)](https://aws.amazon.com/blogs/machine-learning/use-proprietary-foundation-models-from-amazon-sagemaker-jumpstart-in-amazon-sagemaker-studio/)
  * [AWS Deep Learning Containers Images](https://docs.aws.amazon.com/deep-learning-containers/latest/devguide/deep-learning-containers-images.html)
  * [OpenSearch Popular APIs](https://opensearch.org/docs/latest/opensearch/popular-api/)
  * [Using the Amazon SageMaker Studio Image Build CLI to build container images from your Studio notebooks (2020-09-14)](https://aws.amazon.com/blogs/machine-learning/using-the-amazon-sagemaker-studio-image-build-cli-to-build-container-images-from-your-studio-notebooks/)
  * [SageMaker Python SDK - Deploy a Pre-Trained Model Directly to a SageMaker Endpoint](https://sagemaker.readthedocs.io/en/stable/overview.html#deploy-a-pre-trained-model-directly-to-a-sagemaker-endpoint)
  * [AWS CDK TypeScript Example - Custom Resource](https://github.com/aws-samples/aws-cdk-examples/tree/master/typescript/custom-resource)
  * [How to create a Lambda layer using a simulated Lambda environment with Docker](https://aws.amazon.com/premiumsupport/knowledge-center/lambda-layer-simulated-docker/)
    ```
    $ cat <<EOF>requirements-lambda_layer.txt
    > sagemaker==2.188
    > cfnresponse==1.1.2
    > urllib3==1.26.16
    > EOF

    $ docker run -v "$PWD":/var/task "public.ecr.aws/sam/build-python3.10" /bin/sh -c "pip install -r requirements-lambda_layer.txt -t python/lib/python3.10/site-packages/; exit"

    $ zip -r sagemaker-python-sdk-lib.zip python > /dev/null

    $ aws s3 mb s3://my-bucket-for-lambda-layer-packages

    $ aws s3 cp sagemaker-python-sdk-lib.zip s3://my-bucket-for-lambda-layer-packages/pylambda-layer/
    ```
  * [Connect using the EC2 Instance Connect CLI](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-connect-methods.html#ec2-instance-connect-connecting-ec2-cli)
    ```
    $ sudo pip install ec2instanceconnectcli
    $ mssh --region us-east-1 ec2-user@i-001234a4bf70dec41EXAMPLE
    ```
    * Remotely access your Amazon OpenSearch Cluster using SSH tunnel from local machine
      <pre>
      $ mssh --region {<i>region</i>} ec2-user@{<i>bastion-ec2-instance-id</i>} -N -L 9200:vpc-{<i>opensearch-domain-name</i>}-randomidentifier.{<i>region</i>}.es.amazonaws.com:443
      </pre>

## Troubleshooting

  * [(AWS re:Post) Stack deletion stuck as DELETE_IN_PROGRESS](https://repost.aws/questions/QUoEeYfGTeQHSyJSrIDymAoQ/stack-deletion-stuck-as-delete-in-progress)
  * [(Video) How do I delete an AWS Lambda-backed custom resource that’s stuck deleting in AWS CloudFormation?](https://youtu.be/hlJkMoCxR-I?si=NgaNwr9vH15daUBz)
  * [(Stack Overflow)"cannot import name 'DEFAULT_CIPHERS' from 'urllib3.util.ssl_'" on AWS Lambda using a layer](https://stackoverflow.com/questions/76414514/cannot-import-name-default-ciphers-from-urllib3-util-ssl-on-aws-lambda-us)
    * **Error message**:
      ```
      cannot import name 'DEFAULT_CIPHERS' from 'urllib3.util.ssl_' (/opt/python/lib/python3.10/site-packages/urllib3/util/ssl_.py
      ```
    * **Solution**: You’ll need to explicitly pin to `urllib3<2` in your project to ensure `urllib3 2.0` isn’t brought into your environment.
      ```
      urllib3<2
      ```