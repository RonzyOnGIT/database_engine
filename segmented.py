# Database engine using hash indexing, segmenting, and compaction
from typing import TextIO
import json
from pathlib import Path
import os
# Use an in-memory hash map to retrieve contents of file in disk

# each key is mapped to byte offset in data file
# Whenever u want to look up value, use hash map to find offset in data file, seek to that location and read the value
# data is stored on disk as an append-only file


# achieve compaction by throwing away duplicate keys in log, and keeping only most recent update for each key
# a segment is essentially one log file
# segment files are immutable, meaning when merging, generate a new segment
# the merging will be performed using a background worker thread
# while merging is being performed serve data from segment files
# each segment now has its own in-memory index table 

# for now keep .txt but in future try binary format

# For now just give a directory, the program will use this directory and the files inside
# to construct in-memory hash table

# Once this limit is hit, then just perform compaction by removing dupes
# Ofc it has limits, like if every entry is unique then compaction is useless
# For that case, then implement figure it out later
MAX_SEGMENT_SIZE = 128


def compact(data_file: TextIO, index_table: dict) -> dict:
    # loops through file line by line and use a hashmap to keep track of latest seen one
    return {}


# takes directory, and for every directory call_read_data_file, returns list of index tables
def read_segments(paths: list[Path]) -> list[dict]:
    index_tables = []

    for f in paths:
        open_file = open(f, "a+")
        index_tables.append(read_data_file(open_file))
        open_file.close()

    print(f"Index tables for all segments: {index_tables}")

# this now turns into helper function
# reads file with data and build hash map
def read_data_file(data_file: TextIO) -> dict | None:
    index_table = {}

    # get current size
    file_size = os.fstat(data_file.fileno()).st_size

    # if file size is greater than 128, perform compaction
    if file_size > MAX_SEGMENT_SIZE:
        # compaction
        print("hello world")


    data_file.seek(0)

    while True:
        # get seek position before read line
        current_pointer_position = data_file.tell()
        line = data_file.readline()
        
        if not line:
            break

        line_split = line.split(",", 1)
        print(line_split)

        index_table[int(line_split[0])] = current_pointer_position

    return index_table

# returns record given an ID
def get(record_id: int, records: dict, data_file: TextIO) -> dict | None:
    if record_id in records:
        byte_offset = records[record_id]
        data_file.seek(byte_offset)
        record = data_file.readline()
        record_split = record.split(",", 1)
        return json.loads(record_split[1])
    else:
        return None

# records is the in-memory hashmap that stores the id: byte_offset
def insert(records: dict, data_file: TextIO, record_id: int, record: dict) -> None:
    # fail if nothing to insert
    if not record:
        return

    # convert dictionary to json
    string_record = json.dumps(record)

    # convert ID and record object into one entry
    record_entry = str(record_id) + "," + string_record + "\n"

    # file pointer could be pointing somewhere besides end, reset it
    data_file.seek(0, 2)

    # first get offset before saving to hashmap in case of error
    offset = data_file.tell()
    data_file.write(record_entry)
    data_file.flush()
    records[record_id] = offset

    
# create some object type with any fields
def create_entry() -> dict:
    entry = {}

    while True:
        response_key_name = input("key: ")
        print("what data type is the value? ")
        print("[1] int")
        print("[2] bool")
        print("[3] string")
        response_data_type = input("data type: ")

        response = input("value ('t' for True 'f' for false): ")

        if response_data_type == '2':
            response = True if response.lower() == 't' else False

        if response_data_type == '1':
            response = int(response)

        entry[response_key_name] = response

        quit = input("add more? (y or n): ")
        if quit.lower() == 'n':
            break
        
    return entry

def main_loop(records: dict, open_file: TextIO):
    print("-----------------------")
    print("Simple database engine using hashmap\n")
    print("[1] GET Look up a record")
    print("[2] SET Insert or update record")
    print("[3] QUIT Stop db engine")

    while True:
        res = int(input(": "))

        if res == 3:
            print("cya")
            break

        if res == 1:
            record_id = int(input("Enter ID to look up: "))
            record = get(record_id, records, open_file)
            if record is None:
                print("no record found\n")
            else:
                print(record)
        elif res == 2:
            record_id = int(input("enter id: "))
            record = create_entry()
            insert(records, open_file, record_id, record)
        else:
            print("invalid response")

        print("[1] GET Look up a record")
        print("[2] SET Insert or update record")
        print("[3] QUIT Stop db engine")


# for now just make data path 'data'
# dir_path_input = input("enter directory name: ")
# dir_path = Path(f"{dir_path_input}")



data = input("enter file name: ")
data_file = open(f"data/{data}.txt", "a+")
index_table = read_data_file(data_file)
print(index_table)

# paths = []
# for f in dir_path.iterdir():
#     paths.append(f)

# paths.sort()

# print(paths)

# indexes = read_segments(paths)

'''
index_table = read_data_file(data_file)
print(index_table)

main_loop(index_table, data_file)

data_file.close()


# Define the directory
dir_path = Path("path/to/directory")

# List all files and folders inside
for item in dir_path.iterdir():
    print(item.name)
'''