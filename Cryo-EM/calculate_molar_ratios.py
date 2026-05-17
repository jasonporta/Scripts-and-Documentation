#!/usr/bin/python

def calculate_molar_ratio(moles_a, moles_b):
    """
    Calculates the molar ratio between two reactants.

    Args:
        moles_a (float): Number of moles of reactant A.
        moles_b (float): Number of moles of reactant B.

    Returns:
        tuple: Molar ratio of A to B and B to A, or None if either input is zero.
    """
    if moles_a == 0 or moles_b == 0:
        return None

    ratio_a_to_b = moles_a / moles_b
    ratio_b_to_a = moles_b / moles_a

    return ratio_a_to_b, ratio_b_to_a

if __name__ == "__main__":
    try:
        moles_reactant_a = float(input("Enter moles of reactant A: "))
        moles_reactant_b = float(input("Enter moles of reactant B: "))

        ratios = calculate_molar_ratio(moles_reactant_a, moles_reactant_b)

        if ratios:
            print(f"Molar ratio of A to B: {ratios[0]:.2f}")
            print(f"Molar ratio of B to A: {ratios[1]:.2f}")
        else:
            print("Cannot calculate molar ratio when moles of either reactant is zero.")
    except ValueError:
        print("Invalid input. Please enter numeric values for moles.")
