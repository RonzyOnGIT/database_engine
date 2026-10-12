

test = open("data/test.txt", "r")

seek_val = test.tell()
print(seek_val)
test.close()