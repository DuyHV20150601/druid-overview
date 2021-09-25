import os
from utils.common import get_config
from google.cloud import bigquery
import pandas as pd
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchExportSpanProcessor(CloudTraceSpanExporter())
)

GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
CONFIG = get_config("environment.yaml")

PROJECT_ID = CONFIG.get("product_id")

client = bigquery.Client(project=PROJECT_ID)
query = """
SELECT * FROM `gcp-cert-dev.raw.kod_android_free` WHERE DATE(_PARTITIONTIME) = "2021-09-23" LIMIT 10
"""
# query_job = client.query(query)  # Make an API request.

print("The query data:")

table = client.get_table("gcp-cert-dev.raw.kod_android_free")
# print(table.schema)
for field in table.schema:
    print(field.field_type)
    print(field.name)


SchemaField
def get_large_result(query: str, get_df=False):
    if get_df:
        return pd.read_gbq(query, dialect="legacy")

    else:
        # Declare on each function because the configurations of client can be change
        client = bigquery.Client()
        query_config = bigquery.QueryJobConfig(use_legacy_sql=True)
        return client.query(query, project=PROJECT_ID, job_config=query_config)
