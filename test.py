import zlib

f = open("sstables/sstable_1.txt", "rb")

print(zlib.decompress(f.readline()).decode())
f.close()