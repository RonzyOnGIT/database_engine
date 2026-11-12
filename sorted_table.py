# Rather than use only hash map index table, use a self-balancing tree as well as sparse index table
from typing import TextIO
import json
from pathlib import Path
import os
from segment import Segment
from memtable import Memtable
from constants import MAX_SEGMENT_SIZE 
from insert_status import InsertStatus
from sstable import Sstable
import zlib


# achieve compaction by throwing away duplicate keys in log, and keeping only most recent update for each key
# a segment is essentially one log file
# segment files are immutable, meaning when merging, generate a new segment
# the merging will be performed using a background worker thread
# while merging is being performed serve data from segment files
# each segment now has its own in-memory index table 

# for now keep .txt but in future try binary format

# MAX_SEGMENT_SIZE = 128
# MAX_SEGMENT_SIZE = 306

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

def write_to_sstable(sstable: Sstable, memtable: Memtable) -> None:
    # go in order through the memtable and then
    f = open(sstable.path, "ab")
    uncompressed_block = ''
    max_uncompressed_size = 125
    curr_size = 0 # current uncompressed size
    sstable_offset = 0 # current offset in the sstable

    for key, value in memtable.inorder_write(memtable.root):
        # encode and write
        value_json = json.dumps(value)
        entry = str(key) + "," + value_json + "\n"

        # note that the compressed blocks should be like more than a few bytes because any less it get bigger than original from headers
        # and stuff, also maybe just not a lot of redundancy, can also just specify a different compression technique in compress()
        entry_size = len(entry.encode())

        # first check to see if this entry is bigger than the max block size
        if entry_size > max_uncompressed_size:
            # for now drop it, but maybe in the future I can make the max dynamic? Maybe increase it if frequently dropping stuff
            f.close()
            raise ValueError("One of the entries is bigger than current max size for one compressed block")
    
        if curr_size == 0:
            # empty sstable case
            sstable.index_table.append([str(key), sstable_offset])
            # 'register' the first compressed block with the key of the first item and offset of zero
            curr_size += entry_size
            uncompressed_block = entry
        elif curr_size + entry_size <= max_uncompressed_size:
            # current entry fits in current block
            uncompressed_block += entry
            curr_size += entry_size
        else:
            # compress current block and write to sstable, carry over this entry to next block
            compressed_segment = zlib.compress(uncompressed_block.encode())
            f.write(compressed_segment)

            sstable_offset += len(compressed_segment)

            uncompressed_block = entry
            sstable.index_table.append([str(key), sstable_offset])
            curr_size = 0
            curr_size += entry_size

    if curr_size > 0:
        # write any left over stuff
        f.write(zlib.compress(uncompressed_block.encode()))

    f.close()
    return

# returns record given an ID
def get(memtable: Memtable, search_id: int) -> dict | None:
    record = memtable.binary_search(memtable.root, search_id)
    return record

# records is the in-memory hashmap that stores the id: byte_offset
def insert(memtable: Memtable, key: int, value: dict) -> InsertStatus:
    # fail if nothing to insert
    if not value:
        return InsertStatus.FAIL

    status = memtable.insert(key, value)
    if status == InsertStatus.TOO_LARGE:
        # call method to write sstable, then retry again after memtable has been cleared
        return InsertStatus.TOO_LARGE
    return InsertStatus.INSERTED

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

# For now, take in one sstable object and search it, in future, will accept directory and search all sstables
def search_sstable(sstable: Sstable, record_id: int) -> dict | None:
    # assume already looked in memtable, and did not find record
    # perform binary search on the sstable object's index_table attribute which is an array 

    f = open(sstable.path, "rb")

    # nex to work -> this only works if the start of the segment ID matches the id being looked for
    # fix this so that it will look within blocks that it could be in
    # standard binary search
    l, r = 0, len(sstable.index_table) - 1
    while l <= r:
        mid = (l + r) // 2
        mid_id = sstable.index_table[mid][0]
        # sstable index table structure [[record_id, byte_offset], [], ...]
        if mid_id == record_id:
            # have to get size of current block to be able to decompress
            # in order to do this, just look at current offset and compare with next block's offset and take difference
            f.seek(sstable.index_table[mid][1]) # seek to compressed block
            if mid < len(sstable.index_table) - 1:
                current_compressed_size = sstable.index_table[mid + 1][1] - sstable.index_table[mid][1]
                uncompressed_block = zlib.decompress(f.read(current_compressed_size))
                print(f"found matching record: {uncompressed_block.decode()}")
                f.close()
                return
            else:
                f.seek(sstable.index_table[mid][1])
                uncompressed_block = zlib.decompress(f.read())
                print(f"found matching record: {uncompressed_block.decode()}")
                f.close()
                return
        elif record_id > mid_id:
            l = mid + 1
        else:
            r = mid - 1

    f.close()
    return 

def main_loop(memtable: Memtable) -> tuple[Memtable, Sstable]: 
    print("-----------------------")
    print("Simple database engine using hashmap\n")
    print("[1] GET Look up a record")
    print("[2] SET Insert or update record")
    print("[3] QUIT Stop db engine")

    sstable = Sstable(Path("sstables/sstable_1.txt"))
    while True:
        
        res = int(input(": "))

        if res == 3:
            print("cya")
            break

        if res == 1:
            record_id = int(input("Enter ID to look up: "))
            record = get(memtable, record_id)
            if record is None:
                # did not find it in memtable, start looking to see if it exists in sstables
                print("no record found\n")
            else:
                print(record)
        elif res == 2:
            record_id = int(input("enter id: "))
            record = create_entry()
            status = insert(memtable, record_id, record)

            if status == InsertStatus.TOO_LARGE:
                write_to_sstable(sstable, memtable)      
            
                print("Created sstable and dumped current contents of memtable to it")
                memtable = Memtable()
                status = insert(memtable, record_id, record)
                if status == InsertStatus.INSERTED:
                    print("\nNew memtable has been created and populated with previous record attempt")
                    memtable.inorder(memtable.root)
                    search_sstable(sstable, 100)
                else:
                    print("Creation of memtable has failed :(")
        else:
            print("invalid response")

        print("[1] GET Look up a record")
        print("[2] SET Insert or update record")
        print("[3] QUIT Stop db engine")
    return memtable, sstable


if __name__ == '__main__':
    # only need 1 memtable per process
    # can have multiple sstables (segments) 
    sstable_segment = None
    memtable = Memtable()
    print("----Empty Memtable Created!----")
    memtable, sstable_segment = main_loop(memtable)
    memtable.inorder(memtable.root)