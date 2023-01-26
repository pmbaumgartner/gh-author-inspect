import os
from pathlib import Path

import typer
from rich.console import Console

from .queries import (
    discussions_comment_query,
    discussions_query,
    issues_comment_query,
    issues_query,
    user_basics_query,
)
from .utils import (
    _print_http_error,
    discussion_comments_to_table,
    discussions_to_table,
    gh_graphql_query,
    issue_comments_to_table,
    issues_to_table,
    no_data_panel,
    print_token_error,
    print_user_data,
    process_discussion_comments,
    process_discussions,
    process_issue_comments,
    process_issues,
    user_data_to_dict,
)

OAUTH_TOKEN = os.environ.get("GITHUB_TOKEN")

console = Console()


def main(
    repo: str = typer.Argument(..., help="Repository name as 'owner/name'."),
    author: str = typer.Argument(..., help="Username (author) to search for."),
    comments: bool = typer.Option(
        False,
        "--comments",
        "-c",
        help="Include user comments in addition to top-level content in the output",
    ),
    limit_title: int = typer.Option(
        50,
        help="Max length of the string for the title. `0` will not truncate at all.",
    ),
):
    """This tool executes queries against the GitHub Search API for the user
    and repository given. It looks up Issues/PRs and Discussions created by
    the user and optionally also the comments made by the user."""
    if OAUTH_TOKEN is None or OAUTH_TOKEN == "":
        print_token_error()
        raise typer.Exit(1)

    with console.status("Querying GitHub API", spinner="circle"):
        user_data_response = gh_graphql_query(
            user_basics_query,
            {"search_query": f"user:{author}"},
            {"Authorization": f"Bearer {OAUTH_TOKEN}"},
        )
        if not isinstance(user_data_response, dict):
            _print_http_error(user_data_response)
            raise typer.Exit(1)

        user_data_dict = user_data_to_dict(user_data_response)
        if user_data_dict is None:
            console.print(f"No data for user [#7BC4C4]{author}[/#7BC4C4] found")
            raise typer.Exit(1)

        issues_data_response = gh_graphql_query(
            query=issues_query,
            variables={"search_query": f"repo:{repo} author:{author}"},
            headers={"Authorization": f"Bearer {OAUTH_TOKEN}"},
        )
        if not isinstance(issues_data_response, dict):
            _print_http_error(issues_data_response)
            raise typer.Exit(1)

        discussions_data_response = gh_graphql_query(
            query=discussions_query,
            variables={"search_query": f"repo:{repo} author:{author}"},
            headers={"Authorization": f"Bearer {OAUTH_TOKEN}"},
        )
        if not isinstance(discussions_data_response, dict):
            _print_http_error(discussions_data_response)
            raise typer.Exit(1)

        if comments:
            issues_commenter_data_response = gh_graphql_query(
                query=issues_comment_query,
                variables={"search_query": f"repo:{repo} commenter:{author}"},
                headers={"Authorization": f"Bearer {OAUTH_TOKEN}"},
            )
            if not isinstance(issues_commenter_data_response, dict):
                _print_http_error(issues_commenter_data_response)
                raise typer.Exit(1)

            discussions_commenter_data_response = gh_graphql_query(
                query=discussions_comment_query,
                variables={"search_query": f"repo:{repo} commenter:{author}"},
                headers={"Authorization": f"Bearer {OAUTH_TOKEN}"},
            )
            if not isinstance(discussions_commenter_data_response, dict):
                _print_http_error(discussions_commenter_data_response)
                raise typer.Exit(1)

    # Printing
    print_user_data(user_data_dict)
    console.print(f"[bold]Repository:[/bold] {repo}\n")

    issues_data = process_issues(issues_data_response)
    discussions_data = process_discussions(discussions_data_response)

    if len(issues_data) != 0:
        console.print(issues_to_table(issues_data, author, limit_title))
    else:
        console.print(no_data_panel(author, "Issues/PRs"))

    if len(discussions_data) != 0:
        console.print(discussions_to_table(discussions_data, author, limit_title))
    else:
        console.print(no_data_panel(author, "Discussions"))

    if comments:
        issues_comments_data = process_issue_comments(
            issues_commenter_data_response, author
        )
        if len(issues_comments_data) != 0:
            console.print(
                issue_comments_to_table(issues_comments_data, author, limit_title)
            )
        else:
            console.print(no_data_panel(author, "Comments on Issues/PRs"))

        discussion_comments_data = process_discussion_comments(
            discussions_commenter_data_response, author
        )
        if len(discussion_comments_data) != 0:
            console.print(
                discussion_comments_to_table(
                    discussion_comments_data, author, limit_title
                )
            )
        else:
            console.print(no_data_panel(author, "Comments on Discussions"))


def cli():
    typer.run(main)


if __name__ == "__main__":
    typer.run(main)
