"""TASA Main Logic"""

from datetime import datetime
from typing import Callable, List, Dict, Tuple, Optional, Any
import sqlite3
import requests
import urllib3
import db_act
from graphql_helper import get_graphql_mutations, get_graphql_queries

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_last_run_info(cursor: sqlite3.Cursor) -> Optional[datetime]:
    """
    Retrieves the last synchronization timestamp from the last_run table.

    Args:
        cursor: SQLite database cursor.

    Returns:
        datetime or None: The last synchronization datetime,
        or None if not found or an error occurs.
    """
    try:
        cursor.execute(
            "SELECT * FROM last_run ORDER BY last_sync_timestamp DESC LIMIT 1"
        )
        last_run_info = cursor.fetchone()

        if last_run_info:
            last_sync_timestamp = last_run_info[1]
            if isinstance(last_sync_timestamp, str):
                return datetime.strptime(last_sync_timestamp, "%Y-%m-%d %H:%M:%S")

        print("No last run information found.")
        return None

    except (ValueError, IndexError) as error:
        print(f"Error retrieving last run information: {str(error)}")
        return None


def fetch_all_records(cursor: sqlite3.Cursor, env_table_name: str) -> List[Tuple]:
    """
    Fetches all records from the specified environment table that meet the synchronization criteria.

    Args:
        cursor: SQLite database cursor.
        table_name (str): The base name of the table.
        env (str): The environment identifier (e.g., 'dev', 'test', 'prod').

    Returns:
        list: A list of rows retrieved from the table.
    """
    try:
        last_sync_datetime = get_last_run_info(cursor)

        cursor.execute(
            f"""
            SELECT article_id, exp_article_id, locale, title, tags, path, content
            FROM {env_table_name}
            WHERE modified_timestamp IS NULL OR modified_timestamp > ?
        """,
            (last_sync_datetime,),
        )
        return cursor.fetchall()

    except sqlite3.Error as error:
        print(f"Error fetching records: {str(error)}")
        return []


def insert_arva_records(
    db: str, env: str, response_data: Dict, callback: Callable[[str], None] = print
) -> None:
    """
    Inserts ARVA records into the appropriate tables in the SQLite database.

    Args:
        db (str): The database file name.
        env (str): The environment identifier (e.g., 'dev', 'test', 'prod').
        response_data (dict): The ARVA data to insert.
        callback (Callable): A function for logging messages, default is `print`.
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    table_name = db.replace(".db", "")

    try:
        # Insert `pages` data and get page_id
        env_table_name = f"{table_name}_{env}"
        page_id = _insert_page_data(cursor, env_table_name, response_data)

        # Insert related ARVA data
        _delete_records(cursor, env_table_name, page_id)
        _insert_arva_institution(cursor, env_table_name, page_id, response_data)
        _insert_arva_legal_act(cursor, env_table_name, page_id, response_data)
        _insert_arva_page_contact(cursor, env_table_name, page_id, response_data)
        _insert_arva_related_pages(cursor, env_table_name, page_id, response_data)
        _insert_arva_service(cursor, env_table_name, page_id, response_data)

        # Commit changes and notify success
        conn.commit()
        callback(
            f"Data saved successfully in the database for article ID {page_id} "
            f"in environment: {env}"
        )

    except sqlite3.Error as error:
        callback(f"Database error: {str(error)}")
    finally:
        cursor.close()
        conn.close()


def _delete_records(
    cursor: sqlite3.Cursor, env_table_name: str, article_id: int
) -> None:
    """Deletes all records with the given article_id from related tables."""

    tables = [
        f"{env_table_name}_arva_institution",
        f"{env_table_name}_arva_legal_act",
        f"{env_table_name}_arva_page_contact",
        f"{env_table_name}_arva_related_pages",
        f"{env_table_name}_arva_service",
    ]

    print("Deleting records for article_id:", article_id)

    for table in tables:
        cursor.execute(f"DELETE FROM {table} WHERE pageId = ?", (article_id,))

    print("Deletion completed.")


def _insert_page_data(
    cursor: sqlite3.Cursor, env_table_name: str, response_data: Dict
) -> int:
    """Inserts or updates page data in the main table and returns the article_id."""
    page_data = response_data["data"]["pages"]["single"]
    tags = ";".join(
        tag["title"] for tag in page_data["tags"] if isinstance(tag["title"], str)
    )

    cursor.execute(
        f"""
        INSERT INTO {env_table_name} (article_id, locale, title, tags, path, content)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(article_id) DO UPDATE SET
            locale = excluded.locale,
            title = excluded.title,
            tags = excluded.tags,
            path = excluded.path,
            content = excluded.content
        """,
        (
            page_data["id"],
            page_data["locale"],
            page_data["title"],
            tags,
            page_data["path"],
            page_data["content"],
        ),
    )

    return page_data["id"]


def _insert_arva_institution(
    cursor: sqlite3.Cursor, env_table_name: str, page_id: int, response_data: Dict
) -> None:
    """Inserts ARVA institution data."""
    for institution in response_data["data"]["arvaInstitution"][
        "getArvaInstitutionsForPage"
    ]:
        cursor.execute(
            f"""
            INSERT INTO {env_table_name}_arva_institution (
                id, pageId, name, url, isResponsible
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                institution["id"],
                page_id,
                institution["name"],
                institution["url"],
                bool(institution["isResponsible"]),
            ),
        )


def _insert_arva_legal_act(
    cursor: sqlite3.Cursor, env_table_name: str, page_id: int, response_data: Dict
) -> None:
    """Inserts ARVA legal act data."""
    for legal_act in response_data["data"]["arvaLegalAct"]["getLegalActsForPage"]:
        cursor.execute(
            f"""
            INSERT INTO {env_table_name}_arva_legal_act (
                id, pageId, title, url, legalActType, globalId, groupId, versionStartDate
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                legal_act["id"],
                page_id,
                legal_act["title"],
                legal_act["url"],
                legal_act["legalActType"],
                legal_act["globalId"],
                legal_act["groupId"],
                legal_act["versionStartDate"],
            ),
        )


def _insert_arva_page_contact(
    cursor: sqlite3.Cursor, env_table_name: str, page_id: int, response_data: Dict
) -> None:
    """Inserts ARVA page contact data."""
    for contact in response_data["data"]["arvaPageContact"][
        "getArvaPageContactForPage"
    ]:
        cursor.execute(
            f"""
            INSERT INTO {env_table_name}_arva_page_contact (
                id,
                contactId,
                pageId,
                role,
                firstName,
                lastName,
                company,
                email,
                countryCode,
                nationalNumber
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contact["id"],
                contact["contactId"],
                page_id,
                contact["role"],
                contact["firstName"],
                contact["lastName"],
                contact["company"],
                contact["email"],
                contact["countryCode"],
                contact["nationalNumber"],
            ),
        )


def _insert_arva_related_pages(
    cursor: sqlite3.Cursor, env_table_name: str, page_id: int, response_data: Dict
) -> None:
    """Inserts ARVA related pages data."""
    for related_page in response_data["data"]["arvaRelatedPages"][
        "getRelatedPagesForPage"
    ]:
        cursor.execute(
            f"""
            INSERT INTO {env_table_name}_arva_related_pages (id, pageId, title, locale)
            VALUES (?, ?, ?, ?)
            """,
            (
                related_page["id"],
                page_id,
                related_page["title"],
                related_page["locale"],
            ),
        )


def _insert_arva_service(
    cursor: sqlite3.Cursor, env_table_name: str, page_id: int, response_data: Dict
) -> None:
    """Inserts ARVA service data."""
    for service in response_data["data"]["arvaService"]["getArvaServicesForPage"]:
        cursor.execute(
            f"""
            INSERT INTO {env_table_name}_arva_service (id, pageId, name, url)
            VALUES (?, ?, ?, ?)
            """,
            (
                service["id"],
                page_id,
                service["name"],
                service["url"],
            ),
        )


def get_arva_records(
    config: Dict[str, Any], article_ids: str, callback: Callable[[str], None] = print
) -> None:
    """
    Fetches ARVA records for the specified article IDs from a GraphQL API
    and stores them in the database.

    Args:
        config (dict): Configuration containing the database, environment,
        authentication, and GraphQL URL.
        article_ids (str): Comma-separated string of article IDs.
        callback (Callable): A function for logging messages, default is `print`.
    """
    graphql_url = config["graphql_url"]
    headers = {
        "Authorization": f"Bearer {config['bearer_token']}",
        "Content-Type": "application/json",
    }

    arva_records_query = get_graphql_queries()

    for article_id in [int(id.strip()) for id in article_ids.split(",")]:
        variables = {"id": article_id}
        payload = {"query": arva_records_query, "variables": variables}

        try:
            response = requests.post(
                graphql_url,
                json=payload,
                headers=headers,
                verify=False,
                timeout=10,  # nosec:
            )
            response_data = response.json()

            # Check for errors in the response
            if "errors" in response_data:
                unique_errors = set()  # Use a set to collect unique error messages
                for error in response_data["errors"]:
                    error_message = error.get("message", "Unknown error")
                    unique_errors.add(error_message)  # Add error to the set

                # Log unique error messages
                for unique_error in unique_errors:
                    callback(
                        f"Error fetching data for article ID {article_id}: {unique_error}"
                    )

                continue  # Skip processing this article_id if errors are present

            # Process valid data
            if response.status_code == 200 and "data" in response_data:
                insert_arva_records(config["db"], config["env"], response_data)
                callback(f"Records for article ID {article_id} have been inserted.")
            else:
                callback(
                    f"Failed to fetch data for article ID {article_id}: {response.status_code}"
                )

        except requests.RequestException as error:
            callback(f"Error fetching data for article ID {article_id}: {str(error)}")


def prepare_record_variables(row: Tuple) -> Dict:
    """
    Prepares variables for the initial GraphQL mutation for a single record.

    Args:
        row (Tuple): A tuple containing the article data
        (article_id, locale, title, tags, path, content).

    Returns:
        Dict: A dictionary containing the `article_id` and `variables`
        for the GraphQL mutation.
    """
    article_id, exp_article_id, locale, title, tags, path, content = row
    return {
        "article_id": article_id,
        "exp_article_id": exp_article_id,
        "variables": {
            "content": content,
            "description": "",
            "editor": "code",
            "isPrivate": False,
            "isPublished": True,
            "locale": locale,
            "path": path,
            "tags": tags.split(";"),
            "title": title,
        },
    }


def process_record(
    cursor: sqlite3.Cursor,
    env_table_name: str,
    api_config: Dict[str, Any],
    row: Tuple[Any, ...],
    callback: Callable[[str], None] = print,
) -> None:
    """
    Processes a single record by executing the initial and follow-up GraphQL mutations.

    Args:
        cursor (sqlite3.Cursor): The SQLite database cursor.
        env_table_name (str): The environment-specific table name.
        api_config (Dict[str, Any]): API configuration containing the GraphQL
            URL, headers, and mutation strings.
        row (Tuple[Any, ...]): A tuple containing the article data.
        callback (Callable[[str], None]): A callback function for logging. Defaults to `print`.

    Returns:
        None
    """
    try:
        record_data = prepare_record_variables(row)
        article_id = record_data["article_id"]
        exp_article_id = record_data.get("exp_article_id")
        variables = record_data["variables"]

        if not exp_article_id:
            # Execute the initial GraphQL mutation
            response_data = execute_graphql_mutation(api_config, variables, "create")
        else:
            variables["id"] = exp_article_id
            response_data = execute_graphql_mutation(api_config, variables, "update")

        if "errors" in response_data:
            record_id = (
                f"article id: {article_id}"
                if not exp_article_id
                else f"exp_article_id id: {exp_article_id}"
            )
            callback(
                f'Failed to process record {record_id}: {response_data["errors"][0].get("message")}'
            )
            return

        result = response_data["data"]["pages"]

        if "create" in result:
            page_id = result["create"]["page"]["id"]
            callback(
                f'Record {page_id}: {result["create"]["responseResult"]["message"]}'
            )

        if "update" in result:
            page_id = result["update"]["page"]["id"]
            callback(
                f'Record {page_id}: {result["update"]["responseResult"]["message"]}'
            )

        # Update the database with success
        update_record_status(cursor, env_table_name, page_id, variables)

        # Fetch and process related data
        related_data = fetch_related_data(cursor, env_table_name, article_id)
        handle_follow_up_mutation(api_config, page_id, related_data, callback)
    except Exception as error:  # pylint: disable=broad-except
        callback(f"Error while processing record: {error}")


def update_record_status(
    cursor: sqlite3.Cursor, env_table_name: str, page_id: int, variables: Dict[str, str]
) -> None:
    """
    Updates the status of a record in the database after a successful operation.

    Args:
        cursor (sqlite3.Cursor): The SQLite database cursor.
        env_table_name (str): The environment-specific table name.
        page_id (int): The ID of the created page.
        variables (Dict[str, str]): The variables used for the GraphQL
            mutation, including `path` and `locale`.

    Returns:
        None
    """
    try:
        query = (
            f"UPDATE {env_table_name} "
            "SET exp_article_id = ?, status = 'succeeded' "
            "WHERE path = ? AND locale = ?"
        )
        parameters = (
            page_id,
            variables.get("path"),
            variables.get("locale"),
        )

        if not parameters[1] or not parameters[2]:
            raise ValueError("Missing required variables: 'path' or 'locale'")

        cursor.execute(query, parameters)
    except sqlite3.Error as db_error:
        raise RuntimeError(
            f"Database error while updating record status: {db_error}"
        ) from db_error
    except ValueError as value_error:
        raise ValueError(f"Invalid input: {value_error}") from value_error


def execute_graphql_mutation(
    api_config: Dict[str, Any], variables: Dict[str, Any], mutation_type: str
) -> Dict[str, Any]:
    """
    Executes a GraphQL mutation (create or follow-up).

    Args:
        api_config (Dict[str, Any]): API configuration containing the GraphQL
            URL, headers, and mutation strings.
        variables (Dict[str, Any]): Variables for the GraphQL query.
        mutation_type (str): The type of mutation ("create" or "follow_up").

    Returns:
        Dict[str, Any]: The response data from the API call.

    Raises:
        ValueError: If the mutation type is not found in the API configuration.
        RuntimeError: If the request fails or returns a non-200 status code.
    """
    if mutation_type not in api_config:
        raise ValueError(f"Invalid mutation type: {mutation_type}")

    payload = {"query": api_config[mutation_type], "variables": variables}

    try:
        response = requests.post(
            api_config["graphql_url"],
            json=payload,
            headers=api_config["headers"],
            verify=False,  # nosec:
            timeout=10,
        )
        response.raise_for_status()  # Raise an exception for non-2xx responses
        return response.json()
    except requests.exceptions.RequestException as request_error:
        raise RuntimeError(
            f"GraphQL mutation failed: {request_error} - {response.text}"
        ) from request_error


def handle_follow_up_mutation(
    api_config: Dict[str, Any],
    page_id: int,
    related_data: Dict[str, Any],
    callback: Callable[[str], None],
) -> None:
    """
    Handles the follow-up GraphQL mutation to save related data for a page.

    Args:
        api_config (Dict[str, Any]): API configuration containing the GraphQL
            URL, headers, and mutation strings.
        page_id (int): The ID of the created page.
        related_data (Dict[str, Any]): Related data for institutions, legal acts, contacts, etc.
        callback (Callable[[str], None]): A callback function for logging.

    Returns:
        None
    """
    related_data["pageId"] = page_id

    try:
        response_data = execute_graphql_mutation(api_config, related_data, "follow_up")
        if response_data.get("data"):
            callback(f"Successfully processed related records for pageId: {page_id}")
        else:
            callback(f"Failed to process related records for pageId: {page_id}")
    except RuntimeError as error:
        callback(f"Error during follow-up mutation for pageId {page_id}: {error}")


def fetch_related_data(
    cursor: sqlite3.Cursor, env_table_name: str, article_id: int
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetches and formats related data (institutions, legal acts, contacts, etc.)
    from the database for the follow-up GraphQL mutation.

    Args:
        cursor (sqlite3.Cursor): The SQLite database cursor.
        env_table_name (str): The environment-specific table name.
        article_id (int): The article ID.

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary containing related data for
            institutions, legal acts, contacts, related pages, and services.
    """
    # Fetch institution data
    cursor.execute(
        f"""
        SELECT id, name, url, isResponsible
        FROM "{env_table_name}_arva_institution"
        WHERE pageId = ?
        """,
        (article_id,),
    )
    institutions = [
        {
            "id": row[0],
            "name": row[1],
            "url": row[2],
            "isResponsible": bool(row[3]),  # Convert to Boolean
        }
        for row in cursor.fetchall()
    ]

    # Fetch legal act data
    cursor.execute(
        f"""
        SELECT title, url, legalActType, globalId, groupId, versionStartDate
        FROM "{env_table_name}_arva_legal_act"
        WHERE pageId = ?
        """,
        (article_id,),
    )
    legal_acts = [
        {
            "title": row[0],
            "url": row[1],
            "legalActType": row[2],
            "globalId": row[3],
            "groupId": row[4],
            "versionStartDate": row[5],
        }
        for row in cursor.fetchall()
    ]

    # Fetch page contact data
    cursor.execute(
        f"""
        SELECT contactId, role, firstName, lastName, company, email, countryCode, nationalNumber
        FROM "{env_table_name}_arva_page_contact"
        WHERE pageId = ?
        """,
        (article_id,),
    )
    contacts = [
        {
            "id": row[0],
            "role": row[1],
            "firstName": row[2],
            "lastName": row[3],
            "company": row[4],
            "email": row[5],
            "countryCode": row[6],
            "nationalNumber": row[7],
        }
        for row in cursor.fetchall()
    ]

    # Fetch related page data
    cursor.execute(
        f"""
        SELECT id, title, locale
        FROM "{env_table_name}_arva_related_pages"
        WHERE pageId = ?
        """,
        (article_id,),
    )
    related_pages = [
        {"id": row[0], "title": row[1], "locale": row[2]} for row in cursor.fetchall()
    ]

    # Fetch service data
    cursor.execute(
        f"""
        SELECT id, name, url
        FROM "{env_table_name}_arva_service"
        WHERE pageId = ?
        """,
        (article_id,),
    )
    services = [
        {"id": row[0], "name": row[1], "url": row[2]} for row in cursor.fetchall()
    ]

    # Construct and return the related data dictionary
    return {
        "institutionInput": institutions,
        "legalActInput": legal_acts,
        "pageContactInput": contacts,
        "relatedPagesInput": related_pages,
        "serviceInput": services,
    }


def fetch_table_data(
    cursor: sqlite3.Cursor, env_table_name: str, article_id: int, table_suffix: str
) -> List[Dict[str, Any]]:
    """
    Fetches data from a specific related table.

    Args:
        cursor (sqlite3.Cursor): The SQLite database cursor.
        env_table_name (str): The environment-specific table name.
        article_id (int): The article ID.
        table_suffix (str): The suffix for the related table (e.g., "arva_institution").

    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing the rows fetched from the table.
    """
    try:
        table_name = f"{env_table_name}_{table_suffix}"
        query = "SELECT * FROM ? WHERE pageId = ?"
        cursor.execute(
            query,
            (
                table_name,
                article_id,
            ),
        )
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except sqlite3.Error as db_error:
        raise RuntimeError(
            f"Error fetching data from table " f"'{table_name}': {db_error}"
        ) from db_error


def get_api_config(bearer_token: str, graphql_url: str) -> Dict[str, Any]:
    """
    Creates and returns the API configuration required for making GraphQL requests.

    Args:
        bearer_token (str): The bearer token used for API authentication.
        graphql_url (str): The URL of the GraphQL endpoint.

    Returns:
        Dict[str, str]: A dictionary containing the API configuration, including:
            - "graphql_url" (str): The GraphQL endpoint URL.
            - "headers" (dict): HTTP headers for the request, including the Authorization token.
            - "create" (str): The GraphQL mutation string for creating a page.
            - "follow_up" (str): The GraphQL mutation string for follow-up operations.
    """
    if not bearer_token or not graphql_url:
        raise ValueError("Bearer token and GraphQL URL must be provided.")

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }
    create_mutation, follow_up_mutation, update_mutation = get_graphql_mutations()

    return {
        "graphql_url": graphql_url,
        "headers": headers,
        "create": create_mutation,
        "update": update_mutation,
        "follow_up": follow_up_mutation,
    }


def process_records(
    db: str,
    env: str,
    bearer_token: str,
    graphql_url: str,
    callback: Callable[[str], None] = print,
) -> None:
    """
    Processes all records in the database, creating pages and handling related data.

    Args:
        db (str): The database file path.
        env (str): The environment identifier (e.g., dev, test, prod).
        bearer_token (str): The authentication token for API requests.
        graphql_url (str): The GraphQL API URL.
        callback (Callable[[str], None]): A callback function for logging.

    Returns:
        None
    """
    try:
        conn, cursor, table_name = db_act.initialize_db_connection(db)
        api_config = get_api_config(bearer_token, graphql_url)
        env_table_name = f"{table_name}_{env}"

        rows = fetch_all_records(cursor, env_table_name)
        if not rows:
            callback("No records to process.")
            return

        for row in rows:
            try:
                process_record(cursor, env_table_name, api_config, row, callback)
            except Exception as record_error:  # pylint: disable=broad-except
                callback(f"Error processing record: {record_error}")

        conn.commit()
        callback("All records processed.")
    except Exception as general_error:  # pylint: disable=broad-except
        callback(f"Error processing records: {general_error}")
    finally:
        cursor.close()
        conn.close()
