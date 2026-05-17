#!/usr/bin/python

# Convert the output of the 'tree' command to a file named 'tree_output.txt'

import os

def generate_dot_from_tree(tree_output_file, dot_output_file):
    with open(tree_output_file, 'r') as f_in, open(dot_output_file, 'w') as f_out:
        f_out.write("digraph G {\n")
        f_out.write("  rankdir=LR;\n") # Optional: for left-to-right layout

        # Data structure to keep track of current path and parent nodes
        path_stack = []
        node_counter = 0

        for line in f_in:
            line = line.strip()
            if not line:
                continue

            # Determine depth based on leading spaces/indentation
            depth = line.count("    ") # Assuming 4 spaces per level, adjust as needed
            name = line.replace("    ", "") # Remove indentation to get name

            # Handle directory or file
            is_dir = not os.path.splitext(name)[1] # Simple check for file extension

            # Pop from stack if moving up in hierarchy
            while len(path_stack) > depth:
                path_stack.pop()

            # Create node and add to DOT file
            node_id = f"node_{node_counter}"
            f_out.write(f'  {node_id} [label="{name}"];\n')

            # Add edge if there's a parent
            if path_stack:
                parent_node_id = path_stack[-1][1]
                f_out.write(f'  {parent_node_id} -> {node_id};\n')

            # Push current node to stack
            path_stack.append((name, node_id))
            node_counter += 1

        f_out.write("}\n")

# Main 
generate_dot_from_tree("tree_output.txt", "tree_graph.dot")
