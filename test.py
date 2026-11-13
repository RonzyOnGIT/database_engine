import zlib

'''
f = open("sstables/sstable_1.txt", "rb")

print(zlib.decompress(f.readline()).decode())
f.close()
'''


test = [1, 2, 3]

if 2 == len(test) - 1:
    print("last")