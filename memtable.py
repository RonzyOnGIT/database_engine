class Memtable:
    # Red-Black tree implementation
    '''
        Each node needs 3 attributes
            1) color
            2) key (sorted value)
            3) value of actual data
    '''

    def __init__(self):
        # on creation, can just set it to NULL for now
        
        print('hello')

    '''
        Insertion:
            - Two cases to consider:
                1) If parent of new inserted node is black, in the clear
                2) If parent is red, tree might violate Adjacent Red nodes, fix

    ''' 