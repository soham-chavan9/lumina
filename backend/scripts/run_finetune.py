from openai import OpenAI
import os

# Initialize client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Your uploaded file ID from earlier
training_file_id = "file-1FmVbEAD5FVB6b6s9xhsRc"

print("🚀 Starting fine-tuning job for Lumina...\n")

try:
    job = client.fine_tuning.jobs.create(
        training_file=training_file_id,
        model="gpt-3.5-turbo-1106"
    )
    print(f"✅ Fine-tuning job created successfully!")
    print(f"🆔 Job ID: {job.id}")
    print(f"📋 Status: {job.status}")
except Exception as e:
    print(f"❌ Fine-tuning failed: {e}")
