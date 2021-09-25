import json
import time
from pprint import pprint
from typing import List, Dict

import requests
from google.cloud import bigquery

from utils.common import get_config


class Druid:
    overlord_host = "localhost"
    overlord_port = "8081"
    router_host = "localhost"
    router_port = "8888"
    ingestion_url = f"http://{overlord_host}:{overlord_port}/druid/indexer/v1/task"
    query_url = f"http://{router_host}:{router_port}/druid/v2/sql"

    def __init__(self):
        # self.overlord_host = "localhost:8081"  # or router host
        # self.__ingestion_url = "http://localhost:8081/druid/indexer/v1/task"
        pass

    def delete_data(self):
        pass

    @classmethod
    def gen_dimensions_object(
            cls,
            column_name,
            column_type=None,
            create_bitmap_index=True,
            multi_value_handling="sorted_array"
    ):
        return {
            "name": column_name,
            "type": column_type,
            "createBitmapIndex": create_bitmap_index,
            "multiValueHandling": multi_value_handling
        }

    @classmethod
    def gen_field_schema(cls, field_name, field_type="string"):
        return field_name if field_type == "string" else cls.gen_dimensions_object(
            column_name=field_name,
            column_type=field_type
        )

    @classmethod
    def generate_bigquery_table_schema(cls, table: bigquery.Table):
        schema_spec = []
        for field in table.schema:
            if field.field_type == "STRING":
                field_type = "string"
            elif field.field_type == "FLOAT":
                field_type = "float"
            elif field.field_type == "DOUBLE":
                field_type = "double"
            elif field.field_type in ["INTEGER", "TIMESTAMP"]:
                field_type = "long"
            else:
                field_type = field.field_type

            schema_spec.append(cls.gen_field_schema(field_name=field.name, field_type=field_type))

        return schema_spec

    @classmethod
    def gen_timestamp_spec(cls, column, fmt="auto", missing_value=None):
        return {
            "column": column,
            "format": fmt,
            "missing_value": missing_value
        }

    @classmethod
    def gen_dimension_spec(cls, dim_schema: List[Dict], dimension_exclusion=None, spatial_dimension=None):
        # TODO: learn about dimensionExclusions and spatialDimensions
        # link: https://druid.apache.org/docs/latest/ingestion/ingestion-spec.html#inclusions-and-exclusions
        """

        :param dim_schema:
        :param dimension_exclusion:
        :param spatial_dimension:
        :return:
        """
        return {
            "dimensions": dim_schema,
            "dimensionExclusions": dimension_exclusion,
            "spatialDimensions": spatial_dimension
        }

    @classmethod
    def gen_metric_spec(cls, metric_schema: List[Dict] = None):
        # rollup=False => set {"metricsSpec": []}
        return {"metricsSpec":  metric_schema} if metric_schema else metric_schema

    @classmethod
    def gen_granularity_spec(
            cls,
            segment_granularity="day",
            query_granularity=None,
            intervals=None,
            rollup=False):
        """
        link: https://druid.apache.org/docs/latest/ingestion/ingestion-spec.html#granularityspec
        :param segment_granularity: Partition datasource into time chunks
        :param query_granularity: truncating the timestamp
        :param intervals: Specifying which time chunks of segments should be created, for batch ingestion
        :param rollup: Specifying whether ingestion-time rollup should be used or not
        :return:
        """
        return {
            "segmentGranularity": segment_granularity,
            "queryGranularity": query_granularity,
            "intervals": intervals,
            "rollup": rollup
        }

    def gen_transform_spec(self):
        return

    def gen_flatten_spec(self):
        return

    @classmethod
    def gen_csv_io_config(
            cls,
            col_names: List = None,
            task_type="index_parallel",
            find_columns_from_header=True,
            skip_header_rows=0
    ) -> Dict:

        conf = {
            "type": task_type,
            "inputFormat": {
                "type": "csv",
                "findColumnsFromHeader": find_columns_from_header,
                "skipHeaderRows": skip_header_rows
            }
        } if col_names is None else {
            "type": task_type,
            "inputFormat": {
                "type": "csv",
                "columns": col_names,
                "findColumnsFromHeader": False,
                "skipHeaderRows": skip_header_rows
            }
        }

        return conf

    @classmethod
    def gen_local_csv_io_config(cls, _filter="*.csv", _base_dir="/opt/druid/datasource_files", files: List = None):
        csv_io_config = cls.gen_csv_io_config()
        csv_io_config["inputSource"] = {
            "type": "local",
            "filter": _filter,
            "baseDir": _base_dir,
        } if not files else {
            "type": "local",
            "files": files
        }
        return csv_io_config

    def gen_json_io_config(self):
        """
        link: https://druid.apache.org/docs/latest/ingestion/data-formats.html#json
        :return:
        """
        return

    @classmethod
    def gen_gcs_csv_io_config(
            cls,
            uris: List,
            col_names: List = None,
            task_type="index_parallel",
            find_columns_from_header=True,
            skip_header_rows=0
    ):
        """
        link: https://druid.apache.org/docs/latest/ingestion/native-batch.html#google-cloud-storage-input-source
        :return:
        """
        csv_io_conf = cls.gen_csv_io_config(col_names, task_type, find_columns_from_header, skip_header_rows)
        gcs_input_source = {
            "type": "google",
            "uris": uris
        }
        return csv_io_conf.update({
            "inputSource": gcs_input_source
        })

    @classmethod
    def gen_tuning_config(
            cls,
            ingestion_type="index_parallel",
            max_rows_in_memory=1000000,
            # max_bytes_in_memory=
            max_num_concurrent_sub_tasks=2
    ):
        return {
            "type": ingestion_type,
            "maxNumConcurrentSubTasks": max_num_concurrent_sub_tasks,
            "partitionsSpec": {
                "type": "dynamic"
            }
        }

    @classmethod
    def generate_task_spec(
            cls,
            datasource,
            timestamp_spec: Dict,
            dimension_spec: Dict,
            granularity_spec: Dict,
            io_config: Dict,
            tuning_config: Dict,
            task_type="index_parallel",
            metric_spec: Dict = None
    ):

        return {
            "type": task_type,
            "spec": {
                "dataSchema": {
                    "dataSource": datasource,
                    "timestampSpec": timestamp_spec,
                    "dimensionsSpec": dimension_spec,
                    "metricsSpec": metric_spec,
                    "granularitySpec": granularity_spec
                },
                "ioConfig": io_config,
                "tuningConfig": tuning_config
            }
        } if metric_spec else {
            "type": task_type,
            "spec": {
                "dataSchema": {
                    "dataSource": datasource,
                    "timestampSpec": timestamp_spec,
                    "dimensionsSpec": dimension_spec,
                    "granularitySpec": granularity_spec
                },
                "ioConfig": io_config,
                "tuningConfig": tuning_config
            }
        }

    @classmethod
    def get_task_status(cls, task_id: str):
        url = f'http://localhost:8081/druid/indexer/v1/task/{task_id}/status'
        res = requests.get(url)
        return res.json().get('status').get('status'), res.text

    @classmethod
    def ingest_data(cls, spec: Dict):
        headers = {
            'Content-Type': 'application/json'
        }
        res = requests.post(cls.ingestion_url, headers=headers, data=json.dumps(spec))
        res.raise_for_status()
        task_id = res.json().get('task')

        while True:
            status, message = cls.get_task_status(task_id)
            if status == 'RUNNING':
                print("Wait.....")
                time.sleep(30)
            elif status == 'SUCCESS':
                print("Finish.........")
                return
            else:
                raise ValueError(message)

    @classmethod
    def run_query(cls, query: str):
        payload = json.dumps({"query": query})
        headers = {'Content-Type': 'application/json'}
        res = requests.post(cls.query_url, data=payload, headers=headers)
        if res.status_code != 200:
            print(res.text)
            print(query)
        res.raise_for_status()
        return res.json()


CONFIG = get_config("environment.yaml")
PROJECT_ID = CONFIG.get("product_id")

client = bigquery.Client(PROJECT_ID)
druid = Druid
spec = druid.generate_task_spec(datasource="kod",
                                dimension_spec=druid.gen_dimension_spec(
                                    druid.generate_bigquery_table_schema(
                                        client.get_table("gcp-cert-dev.raw.kod_android_free")
                                    )
                                ),
                                io_config=druid.gen_local_csv_io_config(),
                                timestamp_spec=druid.gen_timestamp_spec(column="install_date_utc"),
                                tuning_config=druid.gen_tuning_config(),
                                granularity_spec=druid.gen_granularity_spec())

with open("spec2.json", "w") as fpt:
    json.dump(spec, fpt)

# druid.ingest_data(spec)

pprint(druid.run_query("SELECT * from kod"))
