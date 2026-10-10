# Database engine using hash indexing

# Use an in-memory hash map to retrieve contents of file in disk

# each key is mapped to byte offset in data file
# Whenever u want to look up value, use hash map to find offset in data file, seek to that location and read the value


# data is stored on disk as an append-only file



# data is looking like:
'''
    ID: {
        "name": "John",
        "age": 20
    }
'''