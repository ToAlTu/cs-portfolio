from menu import PHARMACY_MENU, display_menu
from router import route_intent

def display_result(result):
    print("\n--- Routing Decision ---")
    print(f"Primary:    {result['primary_route']}")
    if result['secondary_route']:
        print(f"Secondary:  {result['secondary_route']}")
    print(f"Reasoning:  {result['reasoning']}")
    print(f"Confidence: {result['confidence']}")

if __name__ == "__main__":
    print("=== Phone Menu Router ===")
    display_menu(PHARMACY_MENU)

    while True:
        print("\nDescribe your problem (or type 'quit' to exit):")
        user_input = input().strip()

        if user_input.lower() == "quit":
            print("Goodbye.")
            break

        if not user_input:
            print("Please describe your problem.")
            continue

        print("\nRouting...")
        result, cost = route_intent(user_input, PHARMACY_MENU)
        display_result(result)
        print(f"Cost: ${cost:.6f}")