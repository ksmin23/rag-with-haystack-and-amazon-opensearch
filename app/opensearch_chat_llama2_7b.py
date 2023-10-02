import os
import json
import logging
import sys
from typing import *

import urllib3
urllib3.disable_warnings()

import warnings
warnings.filterwarnings("ignore")

import boto3

from haystack.document_stores import OpenSearchDocumentStore

from haystack.nodes import (
    AnswerParser,
    EmbeddingRetriever,
    PromptNode,
    PromptTemplate
)
from haystack import Pipeline

logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s,%(module)s,%(processName)s,%(levelname)s,%(message)s', level=logging.INFO, stream=sys.stderr)


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


MAX_HISTORY_LENGTH = 5


def _get_credentials(secret_id: str, region_name: str='us-east-1') -> str:
    client = boto3.client('secretsmanager', region_name=region_name)
    response = client.get_secret_value(SecretId=secret_id)
    secrets_value = json.loads(response['SecretString'])
    return secrets_value


def build_chain():
    region = os.environ["AWS_REGION"]
    opensearch_domain_endpoint = os.environ["OPENSEARCH_DOMAIN_ENDPOINT"]
    text2text_model_endpoint = os.environ["TEXT2TEXT_ENDPOINT_NAME"]
    opensearch_secret = os.environ["OPENSEARCH_SECRET"]

    creds = _get_credentials(opensearch_secret, region)
    opensearch_username = creds['username']
    opensearch_password = creds['password']
    opensearch_port = 443

    doc_store = OpenSearchDocumentStore(host=opensearch_domain_endpoint,
                                        port=opensearch_port,
                                        username=opensearch_username,
                                        password=opensearch_password,
                                        embedding_dim=384)

    model_name_or_path = text2text_model_endpoint
    model_kwargs = {
        "aws_region_name": "us-east-1",
        "aws_custom_attributes": {"accept_eula": "true"}
    }

    question_answering = PromptTemplate(prompt="Given the context please answer the question. If the answer is not contained within the context below, say 'I don't know'.\n"
                                                "Context: {join(documents)};\n Question: {query};\n Answer: ",
                                        output_parser=AnswerParser(reference_pattern=r"Document\[(\d+)\]"))

    gen_qa_with_references = PromptNode(default_prompt_template=question_answering,
                                        max_length=200,
                                        model_name_or_path=model_name_or_path,
                                        model_kwargs=model_kwargs)

    embedding_retriever = EmbeddingRetriever(document_store=doc_store,
                                   embedding_model="sentence-transformers/all-MiniLM-L12-v2",
                                   devices=["cpu"],
                                   top_k=5,
                                   progress_bar=False)

    pipe = Pipeline()
    pipe.add_node(component=embedding_retriever, name='Retriever', inputs=['Query'])
    pipe.add_node(component=gen_qa_with_references, name='GenQAWithRefPromptNode', inputs=['Retriever'])

    logger.info(f"\ntype('pipe'): \"{type(pipe)}\"\n")
    return pipe


def run_chain(chain, prompt: str, history=[]):
    result = chain.run(prompt, params={"Retriever": {"top_k": 3}})
    if not "answers" in result.keys():
        return {'answer': "I don't know"}
    answer = result['answers'][0].answer
    documents = result['documents']
    source_documents = [{'source': doc.meta['url']} for doc in documents]
    return {'answer': answer, 'source_documents': source_documents}


if __name__ == "__main__":
    chat_history = []
    qa = build_chain()
    print(bcolors.OKBLUE + "Hello! How can I help you?" + bcolors.ENDC)
    print(bcolors.OKCYAN + "Ask a question, start a New search: or CTRL-D to exit." + bcolors.ENDC)
    print(">", end=" ", flush=True)
    for query in sys.stdin:
        if (query.strip().lower().startswith("new search:")):
            query = query.strip().lower().replace("new search:","")
            chat_history = []
        elif (len(chat_history) == MAX_HISTORY_LENGTH):
            chat_history.pop(0)
        result = run_chain(qa, query, chat_history)
        chat_history.append((query, result["answer"]))
        print(bcolors.OKGREEN + result['answer'] + bcolors.ENDC)
        if 'source_documents' in result:
            print(bcolors.OKGREEN + 'Sources:')
            for d in result['source_documents']:
                print(d['source'])
        print(bcolors.ENDC)
        print(bcolors.OKCYAN + "Ask a question, start a New search: or CTRL-D to exit." + bcolors.ENDC)
        print(">", end=" ", flush=True)
    print(bcolors.OKBLUE + "Bye" + bcolors.ENDC)