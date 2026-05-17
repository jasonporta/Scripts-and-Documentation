#!/usr/bin/python

import os

def display_tree(startpath, indent_level=0, prefix=""):
    """
    Recursively displays the directory tree from the given startpath.
    """
    # Print the current directory/file
    print(f"{prefix}{os.path.basename(startpath)}")

    # If it's a directory, iterate through its contents
    if os.path.isdir(startpath):
        contents = sorted(os.listdir(startpath))
        num_contents = len(contents)

        for i, item in enumerate(contents):
            path = os.path.join(startpath, item)
            is_last = (i == num_contents - 1)
            
            # Determine the new prefix for sub-items
            if is_last:
                new_prefix = prefix + "    "  # No vertical line for the last item
                item_prefix = prefix + "└── "
            else:
                new_prefix = prefix + "│   "
                item_prefix = prefix + "├── "
            
            display_tree(path, indent_level + 1, item_prefix)

if __name__ == "__main__":
    # You can specify a different starting directory as a command-line argument
    # or use the current working directory by default.
    import sys
    if len(sys.argv) > 1:
        start_directory = sys.argv[1]
    else:
        start_directory = "."  # Current directory

    if not os.path.exists(start_directory):
        print(f"Error: Directory '{start_directory}' not found.")
    else:
        print(start_directory) # Print the root directory separately
        display_tree(start_directory)
