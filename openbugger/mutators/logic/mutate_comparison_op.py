import ast
import random

import astor


class AstBug:
    def __init__(self, name):
        self.name = name

    def apply(self, ast):
        raise NotImplementedError()


class ComparisonOperatorTransformer(ast.NodeTransformer):
    def __init__(self):
        self.mapping = {
            ast.Lt: ast.Gt,
            ast.Gt: ast.Lt,
            ast.LtE: ast.GtE,
            ast.GtE: ast.LtE,
            ast.Eq: ast.NotEq,
            ast.NotEq: ast.Eq,
        }
        self.candidates = []
        self.injected_bugs = []

    def visit_Compare(self, node):
        for comparison in node.ops:
            if type(comparison) in self.mapping:
                self.candidates.append(node)
        return node

    def add_injected_bug(self, line, col, original_op, injected_op):
        self.injected_bugs.append(
            {
                "line": line,
                "col": col,
                "original_op": original_op,
                "injected_op": injected_op,
            }
        )

    def apply_Compare(self, num_errors, random_state=None):
        candidates = self.candidates
        if len(candidates) == 0:
            raise ValueError("No candidates found")
        if num_errors > len(candidates):
            raise ValueError(
                f"Number of errors is greater than number of candidates, errors:{num_errors}, candidates:{len(candidates)}"
            )
        rng = random.Random(random_state)
        rng.shuffle(candidates)
        for i in range(num_errors):
            node = candidates[i]
            for comparison in node.ops:
                if type(comparison) in self.mapping:
                    original_op = type(comparison)
                    node.ops[node.ops.index(comparison)] = self.mapping[original_op]()
                    self.add_injected_bug(
                        node.lineno,
                        node.col_offset,
                        original_op.__name__,
                        self.mapping[original_op]().__class__.__name__,
                    )


class IncorrectComparisonOperatorBug(AstBug):
    def __init__(self):
        super().__init__("incorrect_comparison_operator")

    def apply(self, ast, num_errors=1):
        transformer = ComparisonOperatorTransformer()
        transformer.visit(ast)
        transformer.apply_Compare(num_errors)
        return ast, transformer.injected_bugs


if __name__ == "__main__":
    # First step is to parse the script to an AST using the ast module
    script = """
    x == 5
    y != 10
    if x > y:
        print("x is greater than y")
    else:
        print("x is less than or equal to y")
    """
    ast_tree = ast.parse(script)

    # create an instance of the IncorrectComparisonOperatorBug
    bug = IncorrectComparisonOperatorBug()

    # apply the bug to the ast
    bugged_ast, injected_bugs = bug.apply(ast_tree, num_errors=3)

    # use the modified ast to generate the modified script
    modified_script = astor.to_source(bugged_ast)
    print(modified_script)
    print(injected_bugs)
