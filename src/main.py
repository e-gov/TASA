"""TASA Main"""

import os
import helper
import prog
import db_act


def display_actions() -> None:
    """
    Displays the main menu options for the TASA application.
    """
    ascii_art = (
        "████████╗ █████╗ ███████╗ █████╗ \n"
        "╚══██╔══╝██╔══██╗██╔════╝██╔══██╗\n"
        "   ██║   ███████║███████╗███████║\n"
        "   ██║   ██╔══██║╚════██║██╔══██║\n"
        "   ██║   ██║  ██║███████║██║  ██║\n"
        "   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝\n"
    )
    print(ascii_art)
    print("Welcome to TASA, please make your selection.")
    print("Enter 'Q' to quit.\n")
    menu_options = [
        "0. Display available selections.",
        "1. Create a DB file for a project.",
        "2. Copy data from initial table to another (dev, test, prod).",
        "3. Pull data from ARVA.",
        "4. Insert data to ARVA.",
    ]
    for option in menu_options:
        print(option)


def main() -> None:
    """
    Main function to handle the TASA application's user interactions.
    """
    display_actions()

    while True:
        user_input = input("\nMake a selection: ").strip().upper()

        if user_input == "Q":
            print("Exiting program.")
            break
        if user_input == "0":
            display_actions()
        elif user_input == "1":
            handle_create_db()
        elif user_input == "2":
            handle_copy_table()
        elif user_input == "3":
            handle_pull_data()
        elif user_input == "4":
            handle_insert_data()
        else:
            print("Invalid selection. Please choose 1, 2, 3, 4, or Q.")


def handle_create_db() -> None:
    """
    Handles the creation of a new database file for a project.
    """
    while True:
        db_name = input("\nEnter new project name: ").strip().lower()
        if helper.valid_project_name(db_name):
            if not os.path.exists(f"{db_name}.db"):
                db_act.create_db(f"{db_name}.db")
                print(f"Database '{db_name}.db' created successfully.")
                break
            print("Project already exists!")


def handle_copy_table() -> None:
    """
    Handles copying data from the initial table to another environment.
    """
    while True:
        db_name = input("\nEnter existing project name: ").strip().lower()
        if helper.valid_project_name(db_name) and db_act.db_exists(db_name):
            while True:
                source_env = (
                    input("\nSelect source table (dev, test, prod): ").strip().lower()
                )
                target_env = (
                    input("\nSelect target table (dev, test, prod): ").strip().lower()
                )
                if helper.check_target_env(source_env) and helper.check_target_env(
                    target_env
                ):
                    db_act.copy_table(f"{db_name}.db", source_env, target_env)
                    print(
                        f"Data copied from {source_env} to {target_env} for project '{db_name}'."
                    )
                    return


def handle_pull_data() -> None:
    """
    Handles pulling data from ARVAfor a
    specified project and environment.
    """
    while True:
        db_name = input("\nEnter existing project name: ").strip().lower()
        if helper.valid_project_name(db_name) and db_act.db_exists(db_name):
            while True:
                target_env = (
                    input("\nSelect source environment (dev, test, prod): ")
                    .strip()
                    .lower()
                )
                if helper.check_target_env(target_env):
                    token = helper.get_arva_token(target_env)
                    article_ids = input(
                        "Enter ARVA article ID(s), separated by commas: "
                    ).strip()

                    config = {
                        "db": f"{db_name}.db",
                        "env": target_env,
                        "bearer_token": token,
                        "graphql_url": helper.get_env_url(target_env),
                    }

                    prog.get_arva_records(config, article_ids)
                    print(
                        f"Data pulled for project '{db_name}' in environment '{target_env}'."
                    )
                    return


def handle_insert_data() -> None:
    """
    Handles inserting data into ARVA for a specified project and environment.
    """
    while True:
        db_name = input("\nEnter existing project name: ").strip().lower()
        if helper.valid_project_name(db_name) and db_act.db_exists(db_name):
            while True:
                target_env = (
                    input("\nSelect target environment (dev, test, prod): ")
                    .strip()
                    .lower()
                )
                if helper.check_target_env(target_env):
                    token = helper.get_arva_token(target_env)
                    graphql_url = helper.get_env_url(target_env)

                    if not graphql_url:
                        print(
                            f"Error: GraphQL URL for environment '{target_env}' not found."
                        )
                        return

                    prog.process_records(
                        f"{db_name}.db",
                        target_env,
                        token,
                        graphql_url,  # Ensure this is a valid string
                    )
                    print(
                        f"Data inserted for project '{db_name}' in environment '{target_env}'."
                    )
                    return


if __name__ == "__main__":
    main()
