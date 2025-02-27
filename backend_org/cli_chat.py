import requests

BASE_URL = "http://localhost:8000/chat/"

def get_characters():
    response = requests.get(BASE_URL + "characters/")
    if response.status_code == 200:
        characters = response.json().get("characters", [])
        print("\nAvailable AI Characters:")
        for i, char in enumerate(characters, 1):
            print(f"{i}. {char}")
        return characters
    else:
        print("Error fetching characters!")
        return []

def chat_with_ai(user_id, character, message):
    payload = {
        "user_id": user_id,
        "character": character,
        "message": message
    }
    response = requests.post(BASE_URL, json=payload)
    if response.status_code == 200:
        response_data = response.json()
        print(f"\n{character}: {response_data[character]}")
    else:
        print("Error in AI chat:", response.json())

if __name__ == "__main__":
    print("🚀 Welcome to AI Chat CLI!")
    user_id = 1
    characters = get_characters()

    if characters:
        selected_character = input("\nChoose a character by typing its name: ")

        while True:
            message = input("\nYou: ")
            if message.lower() in ["exit", "quit"]:
                print("👋 Exiting AI Chat. Goodbye!")
                break

            chat_with_ai(user_id, selected_character, message)
