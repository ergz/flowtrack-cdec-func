import json
import requests
import boto3
from botocore.exceptions import ClientError
import psycopg2
import pandas as pd
from sqlalchemy import create_engine


db_port = 5432
db_host = "flowtrack-db-devel.ctskaiq8mthm.us-east-1.rds.amazonaws.com"


def get_secret():
    secret_name = "rds!db-1d33e156-ed4e-48fe-869f-ce3af6cb95b6"
    region_name = "us-east-1"
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    return json.loads(get_secret_value_response["SecretString"])


def create_cdec_url(location, sensor, duration):
    return f"https://cdec.water.ca.gov/dynamicapp/req/JSONDataServlet?Stations={location}&SensorNums={sensor}&dur_code={duration}&Start=2024-08-15"


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    try:
        db_secret = get_secret()
        connection_string = f"postgresql://{db_secret['username']}:{db_secret['password']}@{db_host}:{db_port}/flowtrack"

        engine = create_engine(connection_string)
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()

        # get the data to create the urls we will want to query
        cursor.execute(
            """
            select s2.code as station, s.number sensor, duration_code from cdec_queries
                join sensors s on s.id = cdec_queries.sensor_id
                join stations s2 on s2.id = cdec_queries.station_id where is_active;
            """
        )

        rows = cursor.fetchall()
        data_to_download = [
            dict(zip([column[0] for column in cursor.description], row)) for row in rows
        ]

        cursor.close()
        conn.close()

        urls_to_get = []
        for i in data_to_download:
            urls_to_get.append(
                create_cdec_url(i["station"], i["sensor"], i["duration_code"])
            )

        resp_all_urls = [requests.get(u) for u in urls_to_get]
        all_df = [pd.DataFrame.from_dict(json.loads(x.content)) for x in resp_all_urls]
        all_data = pd.concat(all_df)

        all_data.rename(
            columns={
                "stationId": "station_id",
                "durCode": "duration_code",
                "SENSOR_NUM": "sensor_number",
                "date": "datetime",
            }
        )[["station_id", "duration_code", "datetime", "sensor_number", "value"]]

        return {"statusCode": 200, "body": all_data}
    except Exception as e:
        print(f"Error: {e}")
