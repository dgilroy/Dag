import ast

def get_nodes_at(node: ast.AST, col_offset: int) -> list[ast.AST]:
    """
    Recursively finds elements in an AST node that starts at a given column offset

    Multiple items can start at a given col_offset. e.g. "a,b=3,4" @ offset 0 will have Tuple "a,b" and Name "a"

    :param node: The node to search
    :param col_offset: The offset to match
    :returns: A list of nodes that start at the offset
    """

    results = []
    if hasattr(node, 'col_offset') and node.col_offset == col_offset:
        results.append(node)
    for child_node in ast.iter_child_nodes(node):
        results.extend(get_nodes_at(child_node, col_offset))
    return results



def offset_dict(node: ast.AST) -> dict[int, list[ast.AST]]:
    """
    Iterate over an AST node and return a dict of the offsets at which the nodes start

    :param node: The node to search
    :returns: A dict mapping column offsets to their assocated AST nodes
    """

    results = {}

    for item in ast.walk(node):
        if hasattr(item, "col_offset"):
            results.setdefault(item.col_offset, []).append(item)

    return {k: results[k] for k in sorted(results)}