# Database engine using hash indexing
from typing import TextIO
import json
# Use an in-memory hash map to retrieve contents of file in disk

# each key is mapped to byte offset in data file
# Whenever u want to look up value, use hash map to find offset in data file, seek to that location and read the value


# data is stored on disk as an append-only file


# for now assume txt file



# data is looking like:
'''
    ID: {
        "name": "John",
        "age": 20
    }
'''



# returns record given an ID
def get(record_id: int, records: dict, data_file: TextIO) -> dict:
    # first check in our hashsmap that its in there, if not in there then do not return anytthing

    if record_id in records:
        # seek to the file offset
        print("hello")


    return {}





# set()
# return -1 for fail, 1 for success
def insert(records: dict, data_file: TextIO) -> None:

    record_id = int(input("enter new record ID: "))

    record_object = create_entry()

    # fail if nothing to insert
    if not record_object:
        return

    # convert dictionary to json
    string_record = json.dumps(record_object)

    # convert ID and record object into one entry
    record_entry = str(record_id) + "," + string_record + "\n"

    # empty, offset is zero
    if not data_file:
        records[record_id] = 0
    else:
        # not empty, byte offset is the end of file
        records[record_id] = data_file.tell()

    data_file.write(record_entry)
    

def update() -> int:
    return 0


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

        if response_data_type == 2:
            response = True if response.lower() == 't' else False

        if response_data_type == 1:
            response = int(response)

        entry[response_key_name] = response

        quit = input("add more? (y or n): ")
        if quit.lower() == 'n':
            break
        
    return entry



def create_index() -> dict:
    return {}


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
            # get()
            print("get")
        elif res == 2:
            insert(records, open_file)
        else:
            print("invalid response")

        print("[1] GET Look up a record")
        print("[2] SET Insert or update record")
        print("[3] QUIT Stop db engine")



# open file in read and write mode
data = open("data/data.txt", "a+")
data = input("enter file name: ")
data_file = open(f"data/{data}.txt", "a+")

index_table = {}

main_loop(index_table, data_file)

print(data_file.read())
data_file.close()
