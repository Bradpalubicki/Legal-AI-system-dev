#!/usr/bin/env python3
"""
Secure API Key Setup Script
Prompts for API keys without displaying them and updates .env file
"""
import os
import getpass
import re
from pathlib import Path

def update_env_file(openai_key: str, anthropic_key: str):
    """Update .env file with API keys"""
    # Use root .env file (one level up from backend/)
    env_path = Path(__file__).parent.parent / '.env'

    # Read current .env file
    if env_path.exists():
        with open(env_path, 'r') as f:
            content = f.read()
    else:
        content = ""

    # Update or add OpenAI key
    if 'OPENAI_API_KEY=' in content:
        content = re.sub(
            r'OPENAI_API_KEY=.*',
            f'OPENAI_API_KEY={openai_key}',
            content
        )
    else:
        content += f'\nOPENAI_API_KEY={openai_key}\n'

    # Update or add Anthropic key
    if 'ANTHROPIC_API_KEY=' in content:
        content = re.sub(
            r'ANTHROPIC_API_KEY=.*',
            f'ANTHROPIC_API_KEY={anthropic_key}',
            content
        )
    else:
        content += f'\nANTHROPIC_API_KEY={anthropic_key}\n'

    # Write updated content
    with open(env_path, 'w') as f:
        f.write(content)

    print(f"\n✓ API keys have been securely saved to {env_path}")
    print("✓ Keys are NOT displayed in this terminal")
    print("✓ Make sure .env is in your .gitignore file")

def validate_key(key: str, key_type: str) -> bool:
    """Validate API key format"""
    if not key or key.strip() == "":
        return False

    if key_type == "openai":
        # OpenAI keys start with "sk-"
        if not key.startswith("sk-"):
            print("⚠ Warning: OpenAI keys typically start with 'sk-'")
            return True  # Still allow it
    elif key_type == "anthropic":
        # Anthropic keys start with "sk-ant-"
        if not key.startswith("sk-ant-"):
            print("⚠ Warning: Anthropic keys typically start with 'sk-ant-'")
            return True  # Still allow it

    return True

def main():
    print("=" * 70)
    print("       SECURE API KEY SETUP - Legal AI System")
    print("=" * 70)
    print()
    print("This script will securely update your API keys.")
    print("Your input will NOT be visible on screen.")
    print()
    print("Get your API keys from:")
    print("  • OpenAI:    https://platform.openai.com/api-keys")
    print("  • Anthropic: https://console.anthropic.com/settings/keys")
    print()
    print("-" * 70)

    # Get OpenAI API Key (input hidden)
    while True:
        print("\n1. Enter your OpenAI API Key:")
        print("   (Press Enter to skip if you don't have one)")
        openai_key = getpass.getpass("   OpenAI Key (hidden): ").strip()

        if openai_key == "":
            print("   ⚠ Skipping OpenAI key - you can add it later")
            openai_key = "your-real-openai-api-key-here"
            break

        if validate_key(openai_key, "openai"):
            print("   ✓ OpenAI key accepted")
            break
        else:
            print("   ✗ Invalid key format. Please try again.")

    # Get Anthropic API Key (input hidden)
    while True:
        print("\n2. Enter your Anthropic (Claude) API Key:")
        print("   (Press Enter to skip if you don't have one)")
        anthropic_key = getpass.getpass("   Anthropic Key (hidden): ").strip()

        if anthropic_key == "":
            print("   ⚠ Skipping Anthropic key - you can add it later")
            anthropic_key = "your-real-anthropic-api-key-here"
            break

        if validate_key(anthropic_key, "anthropic"):
            print("   ✓ Anthropic key accepted")
            break
        else:
            print("   ✗ Invalid key format. Please try again.")

    # Confirm before saving
    print("\n" + "-" * 70)
    print("\nReady to save API keys to .env file")

    if openai_key == "your-real-openai-api-key-here" and anthropic_key == "your-real-anthropic-api-key-here":
        print("\n⚠ WARNING: Both keys are still placeholders!")
        print("The system will use fallback extraction mode only.")

    confirm = input("\nSave these keys? (yes/no): ").strip().lower()

    if confirm in ['yes', 'y']:
        update_env_file(openai_key, anthropic_key)
        print("\n✓ Setup complete!")
        print("\nNext steps:")
        print("  1. Restart the backend server for changes to take effect")
        print("  2. Test document upload at http://localhost:3000")
        print()
    else:
        print("\n✗ Setup cancelled. No changes made.")
        print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Setup cancelled by user.")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("Please check your permissions and try again.")
