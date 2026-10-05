"""
File: orchestrator/app/services/socratic/safe_math.py
Description: Sandboxed AST-mode arithmetic evaluator (Hotfix 0.2 / Sprint 1).
             Safely evaluates arithmetic expressions using Python's ast parser
             with Fraction representation. Completely avoids eval() and Sympy parse_expr().
             Enforces strict caps on exponent magnitude (<= 10) and value size (<= 1,000,000)
             to eliminate algorithmic denial-of-service and sandbox escapes.
"""

import ast
import re
import logging
from fractions import Fraction
from typing import Optional

logger = logging.getLogger("orchestrator.socratic.safe_math")

MAX_EXPONENT = 10
MAX_VALUE = 1_000_000


def safe_eval_ast(expression: str) -> Optional[Fraction]:
    """
    Safely evaluates an arithmetic expression into an exact Fraction.

    Allowed operations: +, -, *, /, **, unary +, unary -, parentheses.
    Rejects: Any function calls, variable lookups, imports, or unsupported syntax.
    Enforces:
        - Numbers must be <= 1,000,000.
        - Exponents must be between -10 and 10.
        - Division by zero raises ZeroDivisionError (returns None).
    """
    if not expression or not expression.strip():
        return None

    # Canonicalize operator symbols
    clean = (
        expression
        .replace("×", "*")
        .replace("÷", "/")
        .replace("x", "*")
        .replace("^", "**")
        .strip()
    )
    # Strip any trailing equals or labels (e.g. "= ?", "= 15")
    clean = re.sub(r"=.*$", "", clean).strip()

    # Pre-filter: only allow digits, arithmetic operators, decimal dots, parentheses, and spaces
    if not re.match(r"^[\d\s+\-*/().]+$", clean):
        return None

    try:
        tree = ast.parse(clean, mode="eval")

        def evaluate(node: ast.AST) -> Fraction:
            if isinstance(node, ast.Expression):
                return evaluate(node.body)

            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if abs(node.value) > MAX_VALUE:
                    raise ValueError(f"Numeric constant {node.value} exceeds MAX_VALUE {MAX_VALUE}")
                return Fraction(str(node.value))

            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                val = evaluate(node.operand)
                return val if isinstance(node.op, ast.UAdd) else -val

            if isinstance(node, ast.BinOp):
                left = evaluate(node.left)
                right = evaluate(node.right)

                if isinstance(node.op, ast.Add):
                    res = left + right
                elif isinstance(node.op, ast.Sub):
                    res = left - right
                elif isinstance(node.op, ast.Mult):
                    res = left * right
                elif isinstance(node.op, ast.Div):
                    if right == 0:
                        raise ZeroDivisionError("Division by zero in student expression")
                    res = left / right
                elif isinstance(node.op, ast.Pow):
                    # Guard against algorithmic DoS (e.g. 9**9**9)
                    if right > MAX_EXPONENT or right < -MAX_EXPONENT:
                        raise ValueError(f"Exponent {right} exceeds MAX_EXPONENT {MAX_EXPONENT}")
                    res = left ** int(right)
                else:
                    raise ValueError(f"Unsupported binary operator: {type(node.op)}")

                if abs(res) > (MAX_VALUE * 10):
                    raise ValueError("Intermediate result exceeds safe limit")
                return res

            raise ValueError(f"Unsupported AST node type: {type(node)}")

        return evaluate(tree)

    except (ZeroDivisionError, ValueError, SyntaxError) as e:
        logger.debug(f"[SafeMath] Evaluation failed for '{clean}': {e}")
        return None
    except Exception as e:
        logger.warning(f"[SafeMath] Unexpected error evaluating '{clean}': {e}")
        return None


def safe_eval_float(expression: str) -> Optional[float]:
    """Convenience wrapper returning float or None."""
    frac = safe_eval_ast(expression)
    return float(frac) if frac is not None else None
