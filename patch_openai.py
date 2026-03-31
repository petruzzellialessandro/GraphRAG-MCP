import os
import importlib.util

def patch_openai():
    # Dynamically find the openai package in the active environment
    spec = importlib.util.find_spec("openai")
    if not spec or not spec.submodule_search_locations:
        print("❌ OpenAI package not found. Please install dependencies first.")
        return

    # Construct the path to the specific file
    target_file = os.path.join(
        spec.submodule_search_locations[0], 
        "resources", "chat", "completions", "completions.py"
    )

    if not os.path.exists(target_file):
        print(f"❌ File not found at {target_file}")
        return

    # Read the file
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Apply the patch
    target_string = '"max_tokens": max_tokens,'
    if target_string in content:
        new_content = content.replace(target_string, '')
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Successfully patched OpenAI 'max_tokens' issue!")
    else:
        print("⚡ Patch already applied or target string not found.")

if __name__ == "__main__":
    patch_openai()