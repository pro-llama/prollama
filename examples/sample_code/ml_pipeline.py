"""
Example: Machine learning pipeline with cloud credentials.
Author: Dr. Lisa Zhang <lisa.zhang@aistartup.co>
"""

import json
import boto3
from pathlib import Path

# Model API Keys
HUGGINGFACE_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
OPENAI_API_KEY = "sk-ml-team-abc123xyz789"
COHERE_API_KEY = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Cloud Storage
S3_BUCKET_NAME = "aistartup-ml-models-prod"
S3_MODEL_PATH = "s3://aistartup-ml-models-prod/v2/production/"
GCP_BUCKET = "gs://ai-startup-training-data/"
AZURE_CONTAINER = "https://aistartup.blob.core.windows.net/models"

# Database & Cache
FEATURE_STORE_URL = "postgresql://mluser:mlpassword@feature-store.internal:5432/features"
MLFLOW_TRACKING_URI = "https://mlflow.internal.aistartup.co:5000"
WANDB_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Compute resources
AWS_REGION = "us-west-2"
EC2_INSTANCE_TYPE = "p3.8xlarge"
K8S_CLUSTER_ENDPOINT = "https://k8s-ml.aistartup.co:6443"
K8S_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.xxx"

# Data sources
EXTERNAL_DATA_API = "https://data-provider.partner.com/api/v1"
EXTERNAL_API_KEY = "partner-api-key-abc123"
SNOWFLAKE_ACCOUNT = "aistartup.us-east-1"
SNOWFLAKE_USER = "ml_pipeline"
SNOWFLAKE_PASSWORD = "SfPassword123!"


class MLModelManager:
    """Manages ML model lifecycle including training and deployment.
    
    Lead: Dr. Robert Chen (Chief Scientist)
    Data Engineer: Maria Garcia
    Reviewed by: James Wilson (MLOps)
    """

    MODEL_REGISTRY = "s3://aistartup-ml-models-prod/registry/"
    EXPERIMENT_NAME = "fraud_detection_v3"

    def __init__(self, config: dict):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
        )
        self.wandb_key = WANDB_API_KEY
        self.mlflow_uri = MLFLOW_TRACKING_URI

    def download_training_data(self, dataset_name: str) -> str:
        """Download training data from S3."""
        local_path = f"/tmp/{dataset_name}.csv"
        s3_key = f"training-data/{dataset_name}.csv"
        
        self.s3_client.download_file(S3_BUCKET_NAME, s3_key, local_path)
        return local_path

    def upload_model(self, model_path: str, version: str) -> str:
        """Upload trained model to S3 registry."""
        s3_key = f"models/{self.EXPERIMENT_NAME}/{version}/model.pkl"
        self.s3_client.upload_file(model_path, S3_BUCKET_NAME, s3_key)
        return f"s3://{S3_BUCKET_NAME}/{s3_key}"

    def log_experiment(self, metrics: dict, params: dict) -> None:
        """Log experiment metrics to MLflow and Weights & Biases."""
        import wandb
        
        wandb.login(key=self.wandb_key)
        wandb.init(project=self.EXPERIMENT_NAME, config=params)
        wandb.log(metrics)

    def get_feature_vector(self, entity_id: str) -> list:
        """Fetch pre-computed feature vector from feature store."""
        import psycopg2
        
        conn = psycopg2.connect(FEATURE_STORE_URL)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT features FROM entity_features WHERE entity_id = %s",
            (entity_id,),
        )
        result = cursor.fetchone()
        return json.loads(result[0]) if result else []


class InferenceService:
    """Real-time inference service for deployed models."""

    def __init__(self, model_endpoint: str):
        self.endpoint = model_endpoint
        self.api_key = OPENAI_API_KEY

    def predict(self, input_data: dict) -> dict:
        """Make prediction using deployed model."""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        response = requests.post(
            self.endpoint,
            headers=headers,
            json={"instances": [input_data]},
        )
        return response.json()

    def batch_predict(self, input_file: str) -> str:
        """Process batch predictions from input file."""
        output_path = f"/tmp/batch_output_{Path(input_file).stem}.json"
        # Batch processing logic
        return output_path
