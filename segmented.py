# Database engine using hash indexing, segmenting, and compaction
from typing import TextIO
import json
from pathlib import Path
import os
import sys
from segment import Segment

# achieve compaction by throwing away duplicate keys in log, and keeping only most recent update for each key
# a segment is essentially one log file
# segment files are immutable, meaning when merging, generate a new segment
# the merging will be performed using a background worker thread
# while merging is being performed serve data from segment files
# each segment now has its own in-memory index table 

# for now keep .txt but in future try binary format

# MAX_SEGMENT_SIZE = 128
MAX_SEGMENT_SIZE = 306

# have to test this out first
# When file is above threshold limit, creates new compacted file
# In the new compacted file, any duplicate ID entries are removed
# The index_table is the source of truth when writing this new de-duplicated db file
def compact(data_file: TextIO, index_table: dict) -> dict | None:
    original_path = Path(data_file.name)
    segment_num = int(original_path.stem.split("_")[-1])
    new_segment_path = original_path.parent / f"segment_{segment_num + 1}.txt"

    # write to the file using the dictionary as source of truth
    # note that the order in which the new file is written is entirely dependant- 
    # on reading dictionary which the order is arbritrary. i.e. the new file being written cannnot
    # guarantee the same order as the original file (maybe come back to this and figure out workarounds for this although I don't see this being an issue for now)
    file = open(new_segment_path, "w+")
    for id, offset in index_table.items():
        data_file.seek(offset)
        record = data_file.readline()
        file.write(record)

    file.flush()

    updated_index_table = read_data_file(file)
    file.close()
    return updated_index_table


# compact by reading multiple segments and produce one de-duped new segment
# assumes segments are sorted in descending order
# [segment_3.txt, segment_2.txt, segment_1.txt]
# read files in descending order due to fact that segments with higher number hold most recent state for duplicated values
def compact_many(segments: list[Segment]) -> tuple[Path, dict]:
    # returns a new file path for new compacted ones
    new_seg_num = segments[0].seg_num + 1
    compacted_path = segments[0].path.parent / f"segment_{new_seg_num}.txt"
    seen = set()
    # Use x+ in case file aready exists, will raise an error to not write to same file
    new_compact_file = open(compacted_path, "x+")

    for seg in segments:
        f = open(seg.path, "r")
        # open file, now after open, go through the index table for that specific segment and write to new one
        for id, offset in seg.index_table.items():
            if id in seen:
                # already have seen most recent state for this ID, ignore it and move on
                continue
            f.seek(offset)
            record = f.readline()
            new_compact_file.write(record)
            seen.add(id)
        f.close()

    new_compact_file.flush()
    compacted_index_table = read_data_file(new_compact_file)
    new_compact_file.close()
    return compacted_path, compacted_index_table


# split segment file into multiple segments, I think for now it doesnt return anything
# after this gets called, just call read_file to populate new index tables? 
# So what should I return? if after doing segmenting, theres now potentially dozens of new segment files, each of which need their own index_table
# might be better to create a class or something to keep track of all the index tables, good OOP practice as well!
def segment(original_segment: TextIO, index_table: dict) -> None:
    og_path = Path(original_segment.name)
    seg_num = int(og_path.stem.split("_")[-1])

    new_path = og_path.parent / f"segment_{seg_num + 1}.txt"

    # for first run, already know file is full so create new file
    new_file = open(new_path, "w+")

    # keep track of how many new segment files created for file naming
    segment_counter = 1

    for id, offset in index_table.items():
        original_segment.seek(offset)
        record = original_segment.readline()

        # check to see if new file can add this record
        record_size = len(record.encode(original_segment.encoding))
        new_file.flush()
        new_file_size = os.fstat(new_file.fileno()).st_size

        # check if this record itself is bigger than max seg size
        if record_size >= MAX_SEGMENT_SIZE:
            # just ignore the record 笑
            continue

        if new_file_size + record_size > MAX_SEGMENT_SIZE:
            # too big need to create new file and start writing here instead
            new_file.close()
            segment_counter += 1
            new_path = og_path.parent / f"segment_{seg_num + segment_counter}.txt"
            new_file = open(new_path, "w+")
        new_file.write(record)

    new_file.close()


# takes directory, and for every directory call_read_data_file, returns list of index tables
# for now not using thi
def read_segments(dir: Path) -> list[Segment]:
    segments = []

    # in future, handle possibility of not being file rather than just blindly creating an object from this
    for f in dir.iterdir():
        segment_file = Segment(f)
        open_file = open(f, "a+")
        segment_file.index_table = read_data_file(open_file)
        open_file.close()
        segments.append(segment_file)

    return segments

# this now turns into helper function
# reads file with data and build hash map, seeks to zero before anything
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


if __name__ == '__main__':

    print("single file or multi file?\n")
    print("[1]: single file")
    print("[2]: multi file")
    mode = int(input("response:" ))

    if mode == 1:
        data = input("enter file name: ")
        data_file = open(f"data/{data}.txt", "a+")
        index_table = read_data_file(data_file)
        print(f"index table before compaction: {index_table}")

        data_file_size = os.fstat(data_file.fileno()).st_size
        print(f"file size: {data_file_size} bytes")

        # if file size is greater than 128, perform compaction
        if (data_file_size > MAX_SEGMENT_SIZE):
            print("File is large than threshold, performing compaction...\n")
            index_table = compact(data_file, index_table)

        data_file.close()

        compacted_size = os.fstat(data_file.fileno()).st_size
        print(f"new compacted file size: {compacted_size} bytes")
        print(f"index table after compaction: {index_table}")

        # check if after compaction still too big (prob would have to break up the file)
        if compacted_size > MAX_SEGMENT_SIZE:
            print("---File still bigger than max seg size after compaction :(---")
            # split into multiple segments
            segment(data_file, index_table)

        data_file.close()
    elif mode == 2:
        # multi mode so open directory with multiple files
        path = Path(input("\nEnter directory name: "))
        
        if not path.exists():
            print("invalid path, cya")
            sys.exit()

        # path is valid good, now call methods
        segments = read_segments(path)
        # sort descending based on segment number
        segments.sort(key = lambda seg: seg.seg_num, reverse = True)
        for seg in segments:
            print(seg)

        # now test the compaction on multiple segments
        new_path, new_index_table = compact_many(segments)
        print(f"New index table: {new_index_table}")
        segments.clear()
    else:
        print("invalid response, cya")