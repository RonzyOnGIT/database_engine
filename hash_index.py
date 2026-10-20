# Database engine using hash indexing
from typing import TextIO
import json
# Use an in-memory hash map to retrieve contents of file in disk

# each key is mapped to byte offset in data file
# Whenever u want to look up value, use hash map to find offset in data file, seek to that location and read the value
# data is stored on disk as an append-only file

# in future, consider instead of just writing text, to do bytes since windows does \r\n instead of just \n, windows being L no surprise

# reads file with data and build hash map
def read_data_file(data_file: TextIO) -> dict | None:
    index_table = {}

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


def merge():
    return None
    
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


data = input("enter file name: ")
data_file = open(f"data/{data}.txt", "a+")

index_table = read_data_file(data_file)
print(index_table)

main_loop(index_table, data_file)

data_file.close()
