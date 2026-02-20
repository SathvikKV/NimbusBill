import os
import shutil
import argparse

def upload_to_s3_mock(local_path, bucket, s3_prefix):
    """
    Mocks an S3 upload by copying files to a local directory structure.
    SSTructure: ./simulated_s3/{bucket}/{s3_prefix}/
    """
    base_dir = os.path.join("simulated_s3", bucket, s3_prefix)
    os.makedirs(base_dir, exist_ok=True)
    
    filename = os.path.basename(local_path)
    dest_path = os.path.join(base_dir, filename)
    
    shutil.copy2(local_path, dest_path)
    print(f"Uploaded {local_path} to s3://{bucket}/{s3_prefix}/{filename} (Mocked at {dest_path})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Local file to upload")
    parser.add_argument("bucket", help="Target bucket")
    parser.add_argument("prefix", help="S3 Prefix (folder)")
    
    args = parser.parse_args()
    upload_to_s3_mock(args.file, args.bucket, args.prefix)
