import os
import subprocess

# Paths and model
CLEAN_FILE = "backend/data/finetuning/finetune_data_clean.jsonl"
MODEL = "gpt-3.5-turbo-1106"


print("🚀 Uploading dataset to OpenAI...")
file_upload = subprocess.check_output(
    ["openai", "api", "files.create", "-f", CLEAN_FILE, "-p", "fine-tune"]
)
print(file_upload.decode())

file_id = input("📎 Enter the returned file ID (starts with 'file-'): ").strip()

print("\n🎯 Starting fine-tuning job...")
try:
    job_create = subprocess.check_output(
        ["openai", "api", "fine_tuning.jobs.create", "-F", file_id, "-m", MODEL]
    )
    print(job_create.decode())

except subprocess.CalledProcessError as e:
    print("❌ Fine-tuning failed:")
    print(e.output.decode())

print("\n🕒 You can monitor progress with:")
print(f"openai api fine_tuning.jobs.list_events -i <job_id>")
