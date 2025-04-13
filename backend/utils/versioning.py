
# File: versioning.py
# Created: 2025-04-06 16:00:50
# Edited by: King
# Last Edited: 2025-04-06 16:00:50
# Description: Tree version comparison, diffing, and merge suggestion logic.

# versioning.py
# versioning.py
from backend.utils import calculate_match_score

def compare_trees(old_tree, new_tree_data):
    """
    Compare an old tree version with new parsed data.
    Returns a diff summary as a dictionary.
    """
    diff = {}
    # For demonstration, compare individuals by their names.
    old_individuals = {ind.name: ind for ind in getattr(old_tree, "individuals", [])}
    new_individuals = {ind["name"]: ind for ind in new_tree_data.get("individuals", [])}
    
    new_entries = []
    updated_entries = []
    
    for name, new_ind in new_individuals.items():
        if name in old_individuals:
            updated_entries.append(new_ind)
        else:
            new_entries.append(new_ind)
    
    diff["new_individuals"] = new_entries
    diff["updated_individuals"] = updated_entries
    return diff

def suggest_merge(individual1, individual2, session):
    """
    Check for similar individuals and suggest a merge based on past decisions.
    """
    context = {
        "name_similarity": calculate_match_score(individual1, individual2)
        # Future enhancements: add birth date proximity, shared locations, etc.
    }
    if context["name_similarity"] > 85:
        return "accept", context
    return None, context
