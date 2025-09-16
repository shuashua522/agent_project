import uuid

print(str(uuid.uuid4()))
uuid_str = str(uuid.uuid4()).replace("-", "_")
print(uuid_str)