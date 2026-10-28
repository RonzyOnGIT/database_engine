class Memtable:
    # Red-Black tree implementation
    '''
        Each node needs 3 attributes
            1) color
            2) key (sorted value)
            3) value of actual data (not byte offset like hash index)
            4) left
            5) right
            6) parent

    '''
class Node:
    def __init__(self):
        self.color = 'Black'
        self.key = None 
        self.value = None 
        self.left = None 
        self.right = None 
        self.parent = None
