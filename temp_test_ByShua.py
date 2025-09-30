import os

os.environ["HTTP_PROXY"] = "http://127.0.0.1:33210"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:33210"
from langchain.embeddings import HuggingFaceEmbeddings

print("===")
# 明确指定缓存路径（确保有读写权限）
model_name = "sentence-transformers/all-MiniLM-L6-v2"
cache_dir = "F:/PyCharm/SAGE-try/huggingface_cache"  # 使用正斜杠避免路径问题

embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    cache_folder=cache_dir
)
print("end")