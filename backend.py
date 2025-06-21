from dataclasses import dataclass
import re



# ---------- Data Model ----------
@dataclass
class Participant:
    """Represents a participant in the shared expense event."""
    name: str
    amount_spent: float
    weight: float = 1.0
    note: str = ""

# ---------- Helper Functions ----------
def generate_unique_name(name, existing_names):
    """
    Ensures uniqueness of names by appending (n) for the n-th participant with the same name,
    in a case-insensitive manner, and ignoring preceeding/appended whitespace.
    """
    # Strip leading/trailing whitespace from input name
    name = name.strip()

    # Extract the base name from input (ie "Name (1)" -> "Name")
    match = re.match(r"^(.*?)(?: \((\d+)\))?$", name)
    base_name = match.group(1).strip() if match else name

    # Compile pattern to match existing names with the same base name and optional suffix
    pattern = re.compile(rf"^{re.escape(base_name)}(?: \((\d+)\))?$", re.IGNORECASE)

    max_suffix = 1
    for existing in existing_names:
        existing = existing.strip()  # Ensure trimmed comparison
        m = pattern.match(existing)
        if m:
            if m.group(1):
                max_suffix = max(max_suffix, int(m.group(1)) + 1)
            else:
                max_suffix = max(max_suffix, 2)

    if max_suffix == 1:
        return base_name
    else:
        return f"{base_name} ({max_suffix})"

def compute_fair_shares(participants):
    """
    Calculates:
    1. the sum of all spendings
    2. a normalised expense share for weight = 1
    3. the fair share per participant (based on weight)
    """
    total_weight = sum(p.weight for p in participants)
    total_spendings = sum(p.amount_spent for p in participants)
    normalised_share = total_spendings / total_weight if total_weight > 0 else 0.0

    fair_shares = [
        {
            "Name": p.name,
            "Weight": p.weight,
            "Fair Share": round(normalised_share * p.weight, 2)
        }
        for p in participants
    ]
    return total_spendings, normalised_share, fair_shares

def compute_settlements(participants):
    """Determines who owes how much to whom to settle the balances."""
    total_weight = sum(p.weight for p in participants)
    total_spendings = sum(p.amount_spent for p in participants)
    fair_shares = {p.name: total_spendings * p.weight / total_weight for p in participants}
    balances = {p.name: p.amount_spent - fair_shares[p.name] for p in participants}

    # Separate into debtors and creditors
    debtors = sorted([(n, -b) for n, b in balances.items() if b < 0], key=lambda x: x[1])
    creditors = sorted([(n, b) for n, b in balances.items() if b > 0], key=lambda x: x[1])

    # Settlement -- greedy
    transactions = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        debtor, debt = debtors[i]
        creditor, credit = creditors[j]
        amount = min(debt, credit)

        transactions.append({"From": debtor, "To": creditor, "Amount": round(amount, 2)})

        debtors[i] = (debtor, debt - amount)
        creditors[j] = (creditor, credit - amount)

        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1

    return transactions