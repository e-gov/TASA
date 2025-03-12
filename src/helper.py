"""TASA helpers"""

import os
import re
from typing import Callable, Optional


def valid_project_name(name: str, callback=print) -> bool:
    """
    Validates the given project name based on specified rules.

    Args:
        name (str): The project name to validate.
        callback (Callable): Function to handle error messages, default is `print`.

    Returns:
        bool: True if the project name is valid, False otherwise.
    """
    if not name:
        callback("Name can't be empty!")
        return False

    if not re.match(r"^[a-zA-Z0-9_]+$", name):
        callback("Invalid project name (only alphanumeric characters and underscores)!")
        return False

    if name[0].isdigit():
        callback("Project name cannot start with a number!")
        return False

    if name[0] == "_":
        callback("Project name cannot start with an underscore!")
        return False

    if name[-1] == "_":
        callback("Project name cannot end with an underscore!")
        return False

    return True


def get_env_url(env: str) -> Optional[str]:
    """
    Retrieves the GraphQL URL for the given environment.

    Args:
        env (str): The environment identifier (e.g., 'dev', 'test', 'prod').

    Returns:
        Optional[str]: The corresponding GraphQL URL or None if the environment is invalid.
    """
    envs = {
        "dev": "https://arva-main.dev.riaint.ee/graphql",
        "test": "https://arva-main.test.riaint.ee/graphql",
        "prod": "https://arva-main.prod.riaint.ee/graphql",
    }
    return envs.get(env)


def check_target_env(target_env: str, callback: Callable[[str], None] = print) -> bool:
    """
    Validates the selected target environment.

    Args:
        target_env (str): The environment identifier to validate.
        callback (Callable[[str], None]): A callback function for logging errors.

    Returns:
        bool: True if the target environment is valid, False otherwise.
    """
    if target_env in {"dev", "test", "prod"}:
        return True
    callback("Invalid input. Please choose from 'dev', 'test', or 'prod'.")
    return False


def get_arva_token(target_env: str) -> str:
    """
    Retrieves the ARVA token for the given target environment.

    Args:
        target_env (str): The target environment identifier.

    Returns:
        str: The ARVA token for the target environment.
    """
    target_env_upper = target_env.upper()
    token = os.getenv(f"ARVA_TOKEN_{target_env_upper}")

    if token:
        print(f"ARVA_TOKEN_{target_env_upper} found in environment.")
        return token

    token = input("Enter ARVA token: ").strip()
    os.environ[f"ARVA_TOKEN_{target_env_upper}"] = token
    print(f"ARVA_TOKEN_{target_env_upper} saved to the environment.")
    return token
