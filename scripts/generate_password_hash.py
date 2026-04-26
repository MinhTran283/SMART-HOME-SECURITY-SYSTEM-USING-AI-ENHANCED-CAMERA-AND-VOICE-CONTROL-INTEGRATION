from getpass import getpass

from werkzeug.security import generate_password_hash


def main():
    password = getpass("Dashboard password: ")
    confirm = getpass("Confirm password: ")

    if password != confirm:
        raise SystemExit("Passwords do not match")

    print(generate_password_hash(password))


if __name__ == "__main__":
    main()
