#!/home/nermal/venv/bin/python

import os
import graphviz

def create_filesystem_graph(path, graph):
    # Add a node for the current directory
    graph.node(path, label=os.path.basename(path))

    # Iterate through contents
    for item in os.listdir(path):
        item_path = os.path.join(path, item)

        # Add a node for the item
        graph.node(item_path, label=item)

        # Add an edge from parent to child
        graph.edge(path, item_path)

        if os.path.isdir(item_path):
            create_filesystem_graph(item_path, graph)

# Main
dot = graphviz.Digraph(comment='Filesystem Tree')
create_filesystem_graph('/home/nermal/Programs/Scripts', dot) # Replace with your target directory
dot.render('filesystem_tree.dot', view=False) # Renders to 'filesystem_tree.dot.pdf' by default
