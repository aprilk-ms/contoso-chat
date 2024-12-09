from dotenv import load_dotenv
load_dotenv()

from azure.cosmos import CosmosClient
from sys import argv
import os
import pathlib
from contoso_chat.product import product
from azure.identity import DefaultAzureCredential
import prompty
import prompty.azure
from prompty.tracer import trace, Tracer, console_tracer, PromptyTracer
from featuremanagement import FeatureManager
import uuid

# add console and json tracer:
# this only has to be done once
# at application startup
Tracer.add("console", console_tracer)
json_tracer = PromptyTracer()
Tracer.add("PromptyTracer", json_tracer.tracer)


@trace
def get_customer(customerId: str) -> str:
    try:
        url = os.environ["COSMOS_ENDPOINT"]
        client = CosmosClient(url=url, credential=DefaultAzureCredential())
        db = client.get_database_client("contoso-outdoor")
        container = db.get_container_client("customers")
        response = container.read_item(item=str(customerId), partition_key=str(customerId))
        response["orders"] = response["orders"][:2]
        return response
    except Exception as e:
        print(f"Error retrieving customer: {e}")
        return None


@trace
def get_response(customerId, question, chat_history, feature_manager):
    print("getting customer...")
    customer = get_customer(customerId)
    print("customer complete")
    context = product.find_products(question)
    print("products complete")
    print("getting result...")

    session_id = str(uuid.uuid4())

    model_config = {
        "azure_endpoint": os.environ["AZURE_OPENAI_ENDPOINT"],
        "api_version": os.environ["AZURE_OPENAI_API_VERSION"]
    }

    inputs={"question": question, "customer": customer, "documentation": context}

    # Experiment 1: Override model
    variant_model = feature_manager.get_variant("model", session_id)
    if (variant_model is not None):
        model_config["azure_deployment"] = variant_model.configuration

    # Experiment 2: Override system prompt 
    variant_prompt = feature_manager.get_variant("system_prompt", session_id)
    if (variant_prompt is not None):
        inputs["prompt"] = variant_prompt.configuration

    # Experiment 3: Override prompty file
    variant_prompty = feature_manager.get_variant("prompty_version", session_id)
    prompty_file = "chat.prompty"
    if (variant_prompty is not None):
        prompty_file = variant_prompty.configuration

    result = prompty.execute(
        prompty_file,
        inputs=inputs,
        configuration=model_config,
    )
    return {"question": question, "answer": result, "context": context}

if __name__ == "__main__":
    from tracing import init_tracing

    tracer = init_tracing(local_tracing=False)
    get_response(4, "What hiking jackets would you recommend?", [])
    #get_response(argv[1], argv[2], argv[3])