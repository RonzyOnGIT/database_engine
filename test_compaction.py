import pytest 
from segmented import compact, read_data_file
import shutil 
from pathlib import Path


# In future, I will have to instead hardcode path, make it dynamic by using modules or package or something
# So that when I move all test files in a dedicated test directory, wont have to worry about manually updating
# will have to come back to this, because this test is assuming that the order remains the same
# As the code is; however, that is no the guarantee
def test_compaction(tmp_path):
    # this file is over threshold, so compact() shuold create 1 new file and write de-duped records
    original_test_file = Path("data/segment_1.txt")
    new_test_path = tmp_path / "segment_10.txt"

    new_test_file = shutil.copy(original_test_file, new_test_path)

    index_table = {}
    compacted_index_table = {}
    expected_index_table_after_compaction = {}

    with open(new_test_file, "a+") as f:
        index_table = read_data_file(f)
        compacted_index_table = compact(f, index_table)

