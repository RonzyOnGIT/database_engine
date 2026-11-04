# got the code from geeksforgeeks' implementation of red-black tree
from constants import MAX_SEGMENT_SIZE
from insert_status import InsertStatus
import json
class Node:
    # Each node's value will actually store the data, not byte offset like in index table implementation
    def __init__(self, key: int | None = None, value: dict | None = None):
        self.color = "RED"
        self.key = key 
        self.value = value 
        self.left = None 
        self.right = None 
        self.parent = None

# 
class Memtable:
    def __init__(self):
        self.NIL = Node()
        self.NIL.color = "BLACK"
        self.root = self.NIL
        self.size = 0 # tracks size in bytes of current memtable

    def left_rotate(self, x: Node):
        y_node = x.right 
        x.right = y_node.left

        if y_node.left is not self.NIL:
            y_node.left.parent = x

        y_node.parent = x.parent

        if x.parent is None:
            # x is root, set y as new root
            self.root = y_node 
        elif x == x.parent.left:
            x.parent.left = y_node 
        else:
            x.parent.right = y_node

        y_node.left = x
        x.parent = y_node

    def right_rotate(self, x: Node):
        y_node = x.left
        x.left = y_node.right

        if y_node.right is not self.NIL:
            y_node.right.parent = x
        y_node.parent = x.parent

        if x.parent is None:
            self.root = y_node
        elif x == x.parent.right:
            x.parent.right = y_node
        else:
            x.parent.left = y_node

        y_node.right = x
        x.parent = y_node

    def fix_insert(self, k: Node):
        while k!= self.root and k.parent.color == "RED":
            if k.parent == k.parent.parent.left:
                uncle = k.parent.parent.right

                if uncle.color == "RED":
                    k.parent.color = "BLACK"
                    uncle.color = "BLACK"
                    k.parent.parent.color = "RED"
                    k = k.parent.parent
                else:
                    if k == k.parent.right:
                        k = k.parent
                        self.left_rotate(k)
                    k.parent.color = "BLACK"
                    k.parent.parent.color = "RED"
                    self.right_rotate(k.parent.parent)
            else:
                uncle = k.parent.parent.left

                if uncle.color == "RED":
                    k.parent.color = "BLACK"
                    uncle.color = "BLACK"
                    k.parent.parent.color = "RED"
                    k = k.parent.parent
                else:
                    if k == k.parent.left:
                        k = k.parent
                        self.right_rotate(k)
                    k.parent.color = "BLACK"
                    k.parent.parent.color = "RED"
                    self.left_rotate(k.parent.parent)
        self.root.color = "BLACK"  # Root must always be Black

    def insert(self, key: int, value: dict) -> InsertStatus:
        node = Node(key)
        node.value = value
        node.left = self.NIL
        node.right = self.NIL
        parent = None
        current = self.root

        size = len(json.dumps(value).encode('utf-8'))

        # Step 1: Standard Binary Search Tree insertion
        while current != self.NIL:
            parent = current
            # if duplicate, then just overwrite the value. Update new size as well
            if key == current.key:
                prev_size = len(json.dumps(current.value).encode('utf-8'))
                size_diff = size - prev_size 
                if (self.size + size_diff) > MAX_SEGMENT_SIZE:
                    print('Duplicate entry exceeds threshold, keeping original entry')
                    return InsertStatus.TOO_LARGE
                print(f"memtable size: {self.size} bytes")
                current.value = value
                self.size += size_diff
                return InsertStatus.INSERTED
            elif node.key < current.key:
                current = current.left
            else:
                current = current.right

        node.parent = parent

        if (self.size + size) > MAX_SEGMENT_SIZE:
            print('New entry exceeds threshold, writing to disk...')
            return InsertStatus.TOO_LARGE
            # each segment file will have an index table, but will be sparse entries, also compress entries into blocks

        self.size += size
        print(f"memtable size: {self.size} bytes")

        if parent is None:
            self.root = node
        elif node.key < parent.key:
            parent.left = node
        else:
            parent.right = node

        # Step 2: Handle edge cases and fix RB properties
        if node.parent is None:
            node.color = "BLACK"
            return InsertStatus.INSERTED
        if node.parent.parent is None:
            return InsertStatus.INSERTED

        self.fix_insert(node)
        return InsertStatus.INSERTED

    def inorder(self, node: Node):
        if node != self.NIL:
            self.inorder(node.left)
            print(f"key: {node.key}\tvalue: {node.value}")
            self.inorder(node.right)

    # function generator version of inorder used for writing sstables
    def inorder_write(self, node: Node):
        if node != self.NIL:
            yield from self.inorder_write(node.left)
            yield node.key, node.value 
            yield from self.inorder_write(node.right)



    def binary_search(self, node: Node, search_key: int) -> dict | None:
        while node != self.NIL:
            if node.key == search_key:
                return node.value
            elif search_key > node.key:
                node = node.right 
            else:
                node = node.left

        return None