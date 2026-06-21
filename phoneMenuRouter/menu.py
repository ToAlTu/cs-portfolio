PHARMACY_MENU = {
    "business": "CVS Pharmacy",
    "options": [
        {
            "number": "1",
            "label": "Prescription Refills",
            "description": "Request a refill, check refill status, or transfer a prescription from another pharmacy",
            "sub_options": [
                {"number": "1-1", "label": "Request a refill", "description": "Refill an existing prescription on file"},
                {"number": "1-2", "label": "Check refill status", "description": "Check if a prescription is ready for pickup"},
                {"number": "1-3", "label": "Transfer a prescription", "description": "Transfer a prescription from another pharmacy"},
            ]
        },
        {
            "number": "2",
            "label": "Prescription Questions",
            "description": "Questions about dosage, drug interactions, or side effects",
            "sub_options": [
                {"number": "2-1", "label": "Dosage questions", "description": "Questions about how much or how often to take a medication"},
                {"number": "2-2", "label": "Drug interactions", "description": "Questions about combining medications or foods"},
                {"number": "2-3", "label": "Side effects", "description": "Questions or concerns about medication side effects"},
            ]
        },
        {
            "number": "3",
            "label": "Billing and Insurance",
            "description": "Insurance coverage, payments, or billing disputes",
            "sub_options": [
                {"number": "3-1", "label": "Insurance questions", "description": "Questions about whether a medication is covered"},
                {"number": "3-2", "label": "Payment and charges", "description": "Questions about the cost of a prescription"},
                {"number": "3-3", "label": "Dispute a charge", "description": "Dispute an incorrect charge on your account"},
            ]
        },
        {
            "number": "4",
            "label": "Speak with a Pharmacist",
            "description": "General medication questions that require professional advice",
            "sub_options": []
        },
        {
            "number": "5",
            "label": "Store Information",
            "description": "Hours, location, and services offered",
            "sub_options": [
                {"number": "5-1", "label": "Hours and location", "description": "Store hours and address"},
                {"number": "5-2", "label": "Services offered", "description": "Vaccinations, health screenings, and other services"},
            ]
        },
        {
            "number": "6",
            "label": "Speak with a Representative",
            "description": "For anything not covered by the other options",
            "sub_options": []
        }
    ]
}

def format_menu_for_prompt(menu):
    lines = [f"Business: {menu['business']}", "Menu Options:"]
    for option in menu["options"]:
        lines.append(f"{option['number']}. {option['label']} — {option['description']}")
        for sub in option["sub_options"]:
            lines.append(f"   {sub['number']}. {sub['label']} — {sub['description']}")
    return "\n".join(lines)

def display_menu(menu):
    print(f"\n=== {menu['business']} Phone Menu ===")
    for option in menu["options"]:
        print(f"\n{option['number']}. {option['label']}")
        for sub in option["sub_options"]:
            print(f"   {sub['number']}. {sub['label']}")