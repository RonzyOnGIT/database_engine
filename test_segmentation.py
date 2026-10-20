import pytest
from segmented import segment, MAX_SEGMENT_SIZE, read_data_file
import json

# now that read_data_file works for sure, now we can safely use it 
# tmp_path is a Path object unique to each test function
def test_over_threshold_creates_new_segment(tmp_path):
    file = tmp_path / "segment_1.txt"
    records = ""

    # this is 126 bytes, should not create any more files, just remove dupes
    for i in range(6):
        records += f"{i},{json.dumps({"name": "a" * 6})}\n"
    
    file.write_text(records, encoding="utf-8")

    with open(file, "a+") as f:
        index_table = read_data_file()

    index_table = {}
    # after writing to file, need to keep the file open since read_data_file takes open file
    with open(file, "a+") as f:
        index_table = read_data_file(f)

    

json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])


# []
