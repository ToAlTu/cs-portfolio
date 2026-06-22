from menu import PHARMACY_MENU, display_menu
from router import route_intent, generate_clarifying_question, route_with_clarification

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
        total_cost = cost

        if result['confidence'] in ('medium', 'low'):
            print("\nLet me ask one quick question to help route you correctly.")
            question = generate_clarifying_question(user_input, PHARMACY_MENU, result)
            print(f"\n{question}")
            user_answer = input().strip()

            if user_answer:
                print("\nRe-routing with your answer...")
                result, cost = route_with_clarification(user_input, question, user_answer, PHARMACY_MENU)
                total_cost += cost

        display_result(result)
        print(f"Cost: ${total_cost:.6f}")