# deploy_s3.py
import os
import mimetypes
import boto3
from botocore.exceptions import NoCredentialsError

# Configuration
BUCKET_NAME = "supply-chain-frontend-bucket-prod-26042005"
DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend", "dist"))

def upload_directory(path, bucket):
    # Initialize boto3 client
    # Boto3 will automatically pick up credentials from env vars (AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY)
    # or from ~/.aws/credentials.
    s3 = boto3.client('s3')
    
    print(f"Deploying frontend static files from {path} to S3 bucket {bucket}...")
    
    if not os.path.exists(path):
        print(f"Error: Directory {path} does not exist. Did you run 'npm run build' inside frontend?")
        return False
        
    success = True
    for root, dirs, files in os.walk(path):
        for file in files:
            local_file = os.path.join(root, file)
            # Determine relative path for S3 key
            relative_path = os.path.relpath(local_file, path)
            s3_key = relative_path.replace("\\", "/")
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(local_file)
            if mime_type is None:
                mime_type = 'application/octet-stream'
                
            # Extra mapping for common types to be absolutely safe
            if file.endswith('.css'):
                mime_type = 'text/css'
            elif file.endswith('.js'):
                mime_type = 'application/javascript'
            elif file.endswith('.svg'):
                mime_type = 'image/svg+xml'
            elif file.endswith('.html'):
                mime_type = 'text/html'
                
            try:
                s3.upload_file(
                    local_file, 
                    bucket, 
                    s3_key, 
                    ExtraArgs={'ContentType': mime_type}
                )
                print(f"Uploaded: {s3_key} ({mime_type})")
            except NoCredentialsError:
                print("Error: AWS Credentials not found. Please run 'aws configure' or set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY environment variables.")
                return False
            except Exception as e:
                print(f"Failed to upload {s3_key}: {e}")
                success = False
                
    if success:
        print("\n[SUCCESS] Frontend successfully deployed to S3!")
    return success

if __name__ == "__main__":
    upload_directory(DIST_DIR, BUCKET_NAME)
