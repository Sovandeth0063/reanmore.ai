"""
File: services/chemistry_service/app/engine/balancer.py
Description: Chemical equation balancing engine utilizing SymPy linear algebra nullspace matrices
             to calculate exact integer coefficients and compile Socratic steps.
"""

import re
from sympy import Matrix, lcm, Rational

def expand_parentheses(formula: str) -> str:
    """
    Expands parenthesis in a chemical formula.
    Example: 'Ca(OH)2' -> 'CaO2H2'
    """
    pattern = re.compile(r'\(([^)]+)\)(\d+)')
    while True:
        match = pattern.search(formula)
        if not match:
            break
        sub_formula = match.group(1)
        multiplier = int(match.group(2))
        
        # Parse and multiply contents of the parenthesis
        sub_elements = parse_simple_compound(sub_formula)
        expanded_sub = "".join(f"{elem}{count * multiplier}" for elem, count in sub_elements.items())
        
        formula = formula[:match.start()] + expanded_sub + formula[match.end():]
    return formula

def parse_simple_compound(formula: str) -> dict:
    """
    Parses a flat chemical formula (no parentheses).
    Example: 'Fe2O3' -> {'Fe': 2, 'O': 3}
    """
    pattern = re.compile(r'([A-Z][a-z]*)(\d*)')
    elements = {}
    for elem, count in pattern.findall(formula):
        c = int(count) if count else 1
        elements[elem] = elements.get(elem, 0) + c
    return elements

def parse_compound(formula: str) -> dict:
    """
    Cleans, expands parentheses, and parses any chemical formula.
    """
    expanded = expand_parentheses(formula)
    return parse_simple_compound(expanded)

def balance_reaction(equation_str: str) -> dict:
    """
    Balances a chemical equation.
    Example: 'Fe + O2 -> Fe2O3' -> 
    {
       "solution": "4 Fe + 3 O2 -> 2 Fe2O3",
       "steps": [...],
       "success": True,
       "error": None
    }
    """
    steps = [f"Original equation: '{equation_str}'"]
    
    # Normalize reaction arrows
    norm_eq = equation_str.replace('=', '->')
    if '->' not in norm_eq:
        return {
            "solution": None,
            "steps": steps,
            "success": False,
            "error": "Invalid equation format. Must contain '->' or '=' to separate reactants and products."
        }
        
    reactants_part, products_part = norm_eq.split('->')
    reactants = [r.strip() for r in reactants_part.split('+') if r.strip()]
    products = [p.strip() for p in products_part.split('+') if p.strip()]
    
    if not reactants or not products:
        return {
            "solution": None,
            "steps": steps,
            "success": False,
            "error": "Equation must have at least one reactant and one product."
        }

    # Parse all elements
    reactant_compositions = [parse_compound(r) for r in reactants]
    product_compositions = [parse_compound(p) for p in products]
    
    # Extract unique elements
    all_elements = set()
    for comp in reactant_compositions + product_compositions:
        all_elements.update(comp.keys())
    unique_elements = sorted(list(all_elements))
    
    steps.append(f"Reactants identified: {', '.join(reactants)}")
    steps.append(f"Products identified: {', '.join(products)}")
    steps.append(f"Unique elements to balance: {', '.join(unique_elements)}")
    
    # Build systems matrix
    # rows: elements, columns: reactants and negative products
    num_vars = len(reactants) + len(products)
    matrix_data = []
    
    for element in unique_elements:
        row = []
        # Reactants (positive counts)
        for comp in reactant_compositions:
            row.append(comp.get(element, 0))
        # Products (negative counts)
        for comp in product_compositions:
            row.append(-comp.get(element, 0))
        matrix_data.append(row)
        
    # Solve system using null space matrix
    try:
        sym_matrix = Matrix(matrix_data)
        null_space = sym_matrix.nullspace()
        
        if not null_space:
            return {
                "solution": None,
                "steps": steps,
                "success": False,
                "error": "This chemical equation cannot be balanced (no solution exists)."
            }
            
        # Get basis vector
        basis = null_space[0]
        
        # Convert all coefficients to Rational and clear fraction denominators
        rationals = [Rational(val) for val in basis]
        denominators = [r.q for r in rationals]
        scale_factor = lcm(denominators)
        
        coefficients = [int(r * scale_factor) for r in rationals]
        
        # If coefficients are negative, flip them
        if any(c < 0 for c in coefficients):
            coefficients = [-c for c in coefficients]
            
        steps.append(f"Constructed atomic balance matrix of size {len(unique_elements)}x{num_vars}.")
        steps.append(f"Solved null space vector: {rationals}")
        steps.append(f"Multiplied by LCM ({scale_factor}) to get integer coefficients: {coefficients}")
        
        # Formulate output balanced equation
        r_coeffs = coefficients[:len(reactants)]
        p_coeffs = coefficients[len(reactants):]
        
        def format_compound(coeff, compound):
            return f"{coeff} {compound}" if coeff > 1 else compound
            
        balanced_reactants = " + ".join(format_compound(c, comp) for c, comp in zip(r_coeffs, reactants))
        balanced_products = " + ".join(format_compound(c, comp) for c, comp in zip(p_coeffs, products))
        balanced_eq = f"{balanced_reactants} -> {balanced_products}"
        
        steps.append(f"Balanced chemical equation compiled: '{balanced_eq}'")
        
        return {
            "solution": balanced_eq,
            "steps": steps,
            "success": True,
            "error": None
        }
    except Exception as e:
        steps.append(f"Matrix solver error: {str(e)}")
        return {
            "solution": None,
            "steps": steps,
            "success": False,
            "error": f"Failed to solve equation matrix: {str(e)}"
        }
