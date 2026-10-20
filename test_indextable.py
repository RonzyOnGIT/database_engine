import pytest 
import json
from segmented import read_data_file

def test_correct_index_table_creation(tmp_path):
    file = tmp_path / "segment_1.txt"
    records = ""

    for i in range(4):
        records += f"{i},{json.dumps({"name": "c" * 20})}\n"

    # generate some file and write to it that 
    file.write_text(records, encoding="utf-8")

    index_table = {}
    expected_index_table = {
        0: 0,
        1: 35,
        2: 70,
        3: 105
    }

    with open(file, "a+") as f:
        index_table = read_data_file(f)

    assert index_table == expected_index_table, "index table does not match expected index table"