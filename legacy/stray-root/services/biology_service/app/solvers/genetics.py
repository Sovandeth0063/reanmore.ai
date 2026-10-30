"""
File: services/biology_service/app/solvers/genetics.py
Description: Biology genetics solver. Performs DNA transcription to mRNA and mRNA translation 
             to amino acids, or falls back to Gemini AI biology solver with dynamic prompts.
"""

import re
import json
import os
import google.generativeai as genai
from app.prompts import prompt_controller

# Initialize Gemini safely using environment key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# DNA to RNA transcription mapping (Template strand to mRNA)
TRANSCRIPTION_MAP = {"A": "U", "T": "A", "C": "G", "G": "C"}

# Standard Genetic Codon Translation Map
CODON_MAP = {
    "AUG": "Methionine (Start)",
    "UUU": "Phenylalanine", "UUC": "Phenylalanine",
    "UUA": "Leucine", "UUG": "Leucine", "CUU": "Leucine", "CUC": "Leucine", "CUA": "Leucine", "CUG": "Leucine",
    "AUU": "Isoleucine", "AUC": "Isoleucine", "AUA": "Isoleucine",
    "GUU": "Valine", "GUC": "Valine", "GUA": "Valine", "GUG": "Valine",
    "UCU": "Serine", "UCC": "Serine", "UCA": "Serine", "UCG": "Serine", "AGU": "Serine", "AGC": "Serine",
    "CCU": "Proline", "CCC": "Proline", "CCA": "Proline", "CCG": "Proline",
    "ACU": "Threonine", "ACC": "Threonine", "ACA": "Threonine", "ACG": "Threonine",
    "GCU": "Alanine", "GCC": "Alanine", "GCA": "Alanine", "GCG": "Alanine",
    "UAU": "Tyrosine", "UAC": "Tyrosine",
    "CAU": "Histidine", "CAC": "Histidine",
    "CAA": "Glutamine", "CAG": "Glutamine",
    "AAU": "Asparagine", "AAC": "Asparagine",
    "AAA": "Lysine", "AAG": "Lysine",
    "GAU": "Aspartic Acid", "GAC": "Aspartic Acid",
    "GAA": "Glutamic Acid", "GAG": "Glutamic Acid",
    "UGU": "Cysteine", "UGC": "Cysteine",
    "UGG": "Tryptophan",
    "CGU": "Arginine", "CGC": "Arginine", "CGA": "Arginine", "CGG": "Arginine", "AGA": "Arginine", "AGG": "Arginine",
    "GGU": "Glycine", "GGC": "Glycine", "GGA": "Glycine", "GGG": "Glycine",
    "UAA": "STOP", "UAG": "STOP", "UGA": "STOP"
}

def solve_biology_ai(expression: str, grade_level: str) -> dict:
    """
    Compiles biology solver steps using Gemini with grade-level adaptive dynamic prompts.
    """
    if not GEMINI_API_KEY:
        return {
            "solution": None,
            "steps": [expression],
            "success": False,
            "error": "Gemini API key is not configured in the Biology Service environment."
        }
        
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = prompt_controller.get_solver_prompt(expression, grade_level)
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean any accidental markdown block wrappers (e.g. ```json ... ```)
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
            
        steps = json.loads(text)
        if isinstance(steps, list) and len(steps) > 0:
            final_sol = steps[-1] # The last step is the final solution
            return {
                "solution": str(final_sol),
                "steps": steps,
                "success": True,
                "error": None
            }
        else:
            raise ValueError("Parsed output is not a valid list of steps.")
    except Exception as e:
        return {
            "solution": None,
            "steps": [expression],
            "success": False,
            "error": f"Biology AI Solver failed: {str(e)}"
        }

def solve_biology(expression: str, context: dict = None) -> dict:
    """
    Main solve routing for Biology Service.
    Determines if it is a DNA transcription/translation sequence query and runs it.
    Otherwise, falls back to AI solver.
    """
    context = context or {}
    grade_level = context.get("grade_level", "grade_10_12")
    
    query_lower = expression.lower()
    
    # Check if the query contains genetic sequences
    # We find groups of DNA/RNA base characters: A, T, C, G, U with hyphens/spaces
    seq_match = re.search(r'\b([atcgur\- ]{3,})\b', query_lower)
    
    if seq_match and any(w in query_lower for w in ["transcribe", "translate", "dna", "rna", "codon", "sequence"]):
        try:
            raw_seq = seq_match.group(1).upper().replace(" ", "").replace("-", "")
            
            # 1. Transcription (if it contains T, it's DNA. Let's transcribe to RNA)
            is_dna = "T" in raw_seq or not "U" in raw_seq
            
            steps = [f"Original sequence: '{seq_match.group(1)}'"]
            
            if is_dna:
                mrna_seq = "".join(TRANSCRIPTION_MAP.get(base, "N") for base in raw_seq)
                if "N" in mrna_seq:
                    raise ValueError("Sequence contains invalid base characters.")
                steps.append(f"Transcribe DNA sequence to mRNA (A->U, T->A, C->G, G->C): '{mrna_seq}'")
            else:
                mrna_seq = raw_seq
                steps.append(f"Identify mRNA sequence: '{mrna_seq}'")
                
            # 2. Codon splitting
            codons = [mrna_seq[i:i+3] for i in range(0, len(mrna_seq), 3)]
            codons = [c for c in codons if len(c) == 3]
            steps.append(f"Split mRNA into 3-letter codons: {', '.join(codons)}")
            
            # 3. Translation
            amino_acids = []
            translation_details = []
            for codon in codons:
                aa = CODON_MAP.get(codon, "Unknown")
                amino_acids.append(aa)
                translation_details.append(f"Codon '{codon}' translates to '{aa}'")
                if aa == "STOP":
                    break
                    
            steps.extend(translation_details)
            solution = " - ".join(amino_acids)
            steps.append(f"Compiled amino acid chain solution: '{solution}'")
            
            return {
                "solution": solution,
                "steps": steps,
                "success": True,
                "error": None
            }
        except Exception as e:
            pass # Fallback to AI if parsing fails
            
    # Fallback to AI-based step compilation
    return solve_biology_ai(expression, grade_level)
