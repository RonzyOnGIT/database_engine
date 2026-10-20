import json


test_data = ""
for i in range(4):
    test_data += f"{i},{json.dumps({"name": "c" * 20})}\n"

# 128 bytes
size = len(test_data.encode("utf-8"))
print(test_data)
print(f"size of data {size} bytes")

test_file = "testing_r.txt"
with open(test_file, "w") as f:
    f.write(test_data)