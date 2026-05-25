"""Tests for the README-rule classifier."""

import pytest

from mcp_security.atomic_ops.readme_rules import classify_from_readme


def ops_of(hits):
    return {h.atomic_op for h in hits}


@pytest.mark.parametrize(
    "desc",
    [
        "Executes a shell command in a subprocess",
        "Runs an arbitrary script on the host",
        "Evaluates Python code provided by the caller",
        "Spawns a new process",
    ],
)
def test_execute_keywords(desc):
    hits = classify_from_readme("run_cmd", desc, "")
    assert "EXECUTE" in ops_of(hits)


@pytest.mark.parametrize(
    "desc",
    [
        "Permanently deletes a file from disk.",
        "Drops a table from the database.",
        "Removes the resource identified by id.",
        "Destroys the message in the queue.",
    ],
)
def test_delete_keywords(desc):
    hits = classify_from_readme("delete_thing", desc, "")
    assert "DELETE" in ops_of(hits)


@pytest.mark.parametrize(
    "desc",
    [
        "Overwrites an existing file with new content.",
        "Replaces the content of the entry.",
        (
            "Creates a new file or completely overwrites an existing one "
            "with the given content string."
        ),
    ],
)
def test_overwrite_keywords(desc):
    hits = classify_from_readme("write_file", desc, "")
    assert "OVERWRITE" in ops_of(hits)


@pytest.mark.parametrize(
    "desc",
    [
        "Creates a new table in the database.",
        "Alters the schema of an existing table.",
        "Modifies the database schema with DDL statements.",
    ],
)
def test_schema_modify_keywords(desc):
    hits = classify_from_readme("create_table", desc, "")
    assert "SCHEMA_MODIFY" in ops_of(hits)


@pytest.mark.parametrize(
    "desc",
    [
        "Posts a message to a Slack channel.",
        "Sends an email to the specified address.",
        "Publishes a notification to subscribers.",
        "Broadcasts an update to all listeners.",
    ],
)
def test_broadcast_keywords(desc):
    hits = classify_from_readme("post_msg", desc, "")
    assert "BROADCAST" in ops_of(hits)


@pytest.mark.parametrize(
    "desc",
    [
        "Returns the current time as an ISO string.",
        "Computes the hash of the input.",
    ],
)
def test_no_destructive_op_on_benign(desc):
    hits = classify_from_readme("benign", desc, "")
    destructive = {"EXECUTE", "DELETE", "OVERWRITE", "SCHEMA_MODIFY", "BROADCAST"}
    assert ops_of(hits).isdisjoint(destructive)


@pytest.mark.parametrize(
    "name,desc",
    [
        ("insert_row", "Inserts a new row into the table."),
        ("write_file", "Writes a new file with the given content."),
        ("append_insight", "Inserts a single text note into the insights table."),
        ("create_issue", "Creates a new issue in the repository."),
    ],
)
def test_write_keywords(name, desc):
    hits = classify_from_readme(name, desc, "")
    assert "WRITE" in ops_of(hits)


@pytest.mark.parametrize(
    "name,desc",
    [
        (
            "edit_file",
            "Applies one or more find-and-replace operations to an existing file.",
        ),
        ("update_issue", "Updates an existing issue's title or body."),
        ("rename_thing", "Renames the resource."),
    ],
)
def test_modify_keywords(name, desc):
    hits = classify_from_readme(name, desc, "")
    assert "MODIFY" in ops_of(hits)


@pytest.mark.parametrize(
    "name,desc",
    [
        ("move_file", "Moves or renames a file or directory."),
        ("rename_branch", "Renames a branch in the repository."),
    ],
)
def test_move_keywords(name, desc):
    hits = classify_from_readme(name, desc, "")
    assert "MOVE" in ops_of(hits)


@pytest.mark.parametrize(
    "name,desc",
    [
        ("create_directory", "Creates a directory and any missing parent directories."),
        ("create_branch", "Creates a new branch from the given ref."),
        ("create_repository", "Creates a new repository."),
    ],
)
def test_create_keywords(name, desc):
    hits = classify_from_readme(name, desc, "")
    assert "CREATE" in ops_of(hits)


@pytest.mark.parametrize(
    "name,desc",
    [
        ("read_text_file", "Returns the full text content of a file."),
        ("get_file_contents", "Returns the contents of a file at the given ref."),
        ("read_query", "Executes a SQL SELECT statement and returns rows."),
        ("get_channel_history", "Returns the most recent N messages from a channel."),
    ],
)
def test_read_keywords(name, desc):
    hits = classify_from_readme(name, desc, "")
    assert "READ" in ops_of(hits)


@pytest.mark.parametrize(
    "name,desc",
    [
        ("search_files", "Finds files matching a glob pattern within a directory."),
        ("search_code", "Runs GitHub code search across every repository."),
        ("search_files_v2", "Searches the index for matching paths."),
    ],
)
def test_search_keywords(name, desc):
    hits = classify_from_readme(name, desc, "")
    assert "SEARCH" in ops_of(hits)


@pytest.mark.parametrize(
    "name,desc",
    [
        ("get_file_info", "Returns metadata about a file: size, timestamps, type."),
        ("describe_table", "Returns the CREATE TABLE DDL for a specific table."),
        ("get_user_profile", "Returns the detailed Slack profile for a single user."),
    ],
)
def test_metadata_keywords(name, desc):
    hits = classify_from_readme(name, desc, "")
    assert "METADATA" in ops_of(hits)


@pytest.mark.parametrize(
    "name,desc",
    [
        ("list_directory", "Lists the immediate contents of a directory."),
        ("list_tables", "Returns the names of all user tables in the database."),
        ("list_channels", "Lists public channels in the workspace."),
        ("list_branches", "Lists all branches in the repository."),
    ],
)
def test_list_keywords(name, desc):
    hits = classify_from_readme(name, desc, "")
    assert "LIST" in ops_of(hits)
