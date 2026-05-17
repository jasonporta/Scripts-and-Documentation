#!/usr/bin/python

import subprocess
import sys
import getpass
import re

# Error handling function
def run(cmd):
    """Run a system command and exit on errors."""
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)

# Check password strength function
def strong_password(password):
    """Check password meets the requirements using regular expressions."""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

# Prompt user for password function
def prompt_for_password():
    """Prompt the user for strong a password.
    Only return the password when the requirements are met"""
    while True:
        pw1 = getpass.getpass("\nEnter password: ")
        pw2 = getpass.getpass("Confirm password: ")

        if pw1 != pw2:
            print("Passwords do not match. Try again.")
            continue

        if not strong_password(pw1):
            print("\nError: Password must meet the following requirements:")
            print(" - At least 8 characters")
            print(" - Uppercase letter")
            print(" - Lowercase letter")
            print(" - Number")
            print(" - Special character")
            continue

        return pw1

# Create user function
def create_user(user):
    """Prompt user for username"""

    print(f"\nCreating user '{user}'...\n")

    """Print menu for password prompt"""
    print("Now enter a password that meets the following requirements: ")
    print(" - At least 8 characters")
    print(" - Uppercase letter")
    print(" - Lowercase letter")
    print(" - Number")
    print(" - Special character")

    password = prompt_for_password()

    # Create the user and home directory
    run(["sudo", "useradd", "-m", user])

    # Set password using chpasswd
    p = subprocess.Popen(["sudo", "chpasswd"],
                         stdin=subprocess.PIPE,
                         text=True)

    p.communicate(f"{user}:{password}")
    print(f"\nUser {user} has been created successfully.")

# Delete user function
def delete_user(user):
    print(f"\nDeleting user '{user}'...")
    confirm = input(f"Are you sure you want to delete '{user}'? (y/n): ").lower()
    if confirm != "y":
        print("Cancelled.")
        return

    run(["sudo", "userdel", "-r", user])
    print(f"\nUser {user} has been deleted successfully.")

# Begin main function
if __name__ == "__main__":
    """Main function"""
    while True:
        print("\nAdmin User Management")
        print("=========================")
        print("1. Create new user")
        print("2. Delete existing user")
        print("3. Exit \n")

        choice = input("Select an option (1-3): ").strip()

        if choice == '1':
            user = input("Enter the username: ").strip()
            create_user(user)
        elif choice == '2':
            user = input("Enter the username: ").strip()
            delete_user(user)
        elif choice == '3':
            print("\nExiting program... \n")
            break
        else:
            print("Invalid choice. Please try again.")


