# Rather than use only hash map index table, use a self-balancing tree as well as sparse index table
from typing import TextIO
import json
from pathlib import Path
import os
import sys
from segment import Segment
from memtable import Memtable

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
def get(memtable: Memtable, search_id: int) -> dict | None:
    record = memtable.binary_search(memtable.root, search_id)
    return record

# records is the in-memory hashmap that stores the id: byte_offset
def insert(memtable: Memtable, key: int, value: dict) -> None:
    # fail if nothing to insert
    if not value:
        return

    memtable.insert(key, value)
    
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

def main_loop(memtable: Memtable):
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
            if record is None:
                print("no record found\n")
            else:
                print(record)
        elif res == 2:
            record_id = int(input("enter id: "))
            record = create_entry()
            # figure out what to do with duplicate entries
            insert(memtable, record_id, record)
        else:
            print("invalid response")

        print("[1] GET Look up a record")
        print("[2] SET Insert or update record")
        print("[3] QUIT Stop db engine")


if __name__ == '__main__':
    # only need 1 memtable per process
    # can have multiple segments 
    memtable = Memtable()
    print("----Empty Memtable Created!----")
    main_loop(memtable)
    memtable.inorder(memtable.root)