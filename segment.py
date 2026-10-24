from pathlib import Path
class Segment:
    # class that represents one segment
    def __init__(self, path: Path):
        self.path = path
        self.index_table = {}
        self.file_name = path.stem
        self.seg_num = int(path.stem.split("_")[-1])

    def __str__(self):
        return f"File name: {self.file_name}\tFile index: {self.index_table}\tSeg num: {self.seg_num}\tFile path: {self.path}"
