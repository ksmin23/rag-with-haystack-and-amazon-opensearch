import os
import argparse
import glob
import json
import logging
import sys
import time

import warnings
warnings.filterwarnings("ignore") # avoid printing out absolute paths

import boto3

from haystack.document_stores import OpenSearchDocumentStore
from haystack.nodes import (
    JsonConverter,
    PreProcessor,
    EmbeddingRetriever
)

from haystack import Pipeline

# from opensearchpy.client import OpenSearch
from opensearchpy import (
    OpenSearch,
    RequestsHttpConnection
)

logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s,%(module)s,%(processName)s,%(levelname)s,%(message)s', level=logging.INFO, stream=sys.stderr)


def get_credentials(secret_id: str, region_name: str='us-east-1') -> str:
    """
    Retrieve credentials password for given username from AWS SecretsManager
    """

    client = boto3.client('secretsmanager', region_name=region_name)
    response = client.get_secret_value(SecretId=secret_id)
    secrets_value = json.loads(response['SecretString'])

    return secrets_value


def check_if_index_exists(index_name: str, region: str, host: str, http_auth: Tuple[str, str]) -> OpenSearch:
    #update the region if you're working other than us-east-1

    aos_client = OpenSearch(
        hosts=[{'host': host.replace("https://", ""), 'port': 443}],
        http_auth=http_auth,
        use_ssl=True,
        verify_certs=True,
        connection_class = RequestsHttpConnection
    )
    exists = aos_client.indices.exists(index_name)
    logger.info(f"index_name={index_name}, exists={exists}")
    return exists


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--opensearch-endpoint", type=str, default=None)
    parser.add_argument("--opensearch-port", type=int, default=443)
    parser.add_argument("--opensearch-secret-id", type=str, default=None)
    parser.add_argument("--aws-region", type=str, default="us-east-1")
    parser.add_argument("--input-data-dir", type=str, default="/opt/ml/processing/input")

    args, _ = parser.parse_known_args()
    logger.info("Received arguments {}".format(args))

    # list all the files
    files = glob.glob(os.path.join(args.input_data_dir, "*.json"))
    logger.info(f"there are {len(files)} files to process in the {args.input_data_dir} folder")

    # retrieve secret to talk to opensearch
    secret = get_credentials(args.opensearch_secret_id, args.aws_region)

    OPENSEARCH_HOST = args.opensearch_endpoint
    OPENSEARCH_PORT = 443
    OPENSEARCH_USERNAME = secret['username']
    OPENSEARCH_PASSWORD = secret['password']

    # Stage one: read all the docs, split them into chunks.
    st = time.time()
    logger.info('Loading documents ...')

    # first check if index exists, if it does then call the add_documents function
    # otherwise call the from_documents function which would first create the index
    # and then do a bulk add. Both add_documents and from_documents do a bulk add
    # but it is important to call from_documents first so that the index is created
    # correctly for K-NN
    http_auth = (secret['username'], secret['password'])
    OPENSEARCH_INDEX_NAME = "document"
    index_exists = check_if_index_exists(OPENSEARCH_INDEX_NAME,
                                         args.aws_region,
                                         args.opensearch_cluster_domain,
                                         http_auth)

    if index_exists:
        et = time.time()
        logger.info(f"index={args.opensearch_index_name} does exists, not going to call add_documents")
        logger.info(f'run time in seconds: {et-st:.2f}')
        logger.info("all done")
        sys.exit(0)

    doc_store = OpenSearchDocumentStore(host=OPENSEARCH_HOST,
                                        port=OPENSEARCH_PORT,
                                        username=OPENSEARCH_USERNAME,
                                        password=OPENSEARCH_PASSWORD,
                                        embedding_dim=384)

    converter = JsonConverter()

    preprocessor = PreProcessor(
        clean_empty_lines=True,
        split_by='word',
        split_respect_sentence_boundary=True,
        split_length=80,
        split_overlap=20
    )

    retriever = EmbeddingRetriever(
        document_store=doc_store,
        embedding_model="sentence-transformers/all-MiniLM-L12-v2",
        devices=["cpu"],
        top_k=5
    )

    indexing_pipeline = Pipeline()
    indexing_pipeline.add_node(component=converter, name="Converter", inputs=["File"])
    indexing_pipeline.add_node(component=preprocessor, name="PreProcessor", inputs=["Converter"])
    indexing_pipeline.add_node(component=retriever, name="Retriever", inputs=["PreProcessor"])
    indexing_pipeline.add_node(component=doc_store, name="DocumentStore", inputs=["Retriever"])

    indexing_pipeline.run(file_paths=files)

    et = time.time()
    logger.info(f'run time in seconds: {et-st:.2f}')
    logger.info("all done")


if __name__ == "__main__":
    main()
