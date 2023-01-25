from datetime import datetime, timezone
from textwrap import shorten
from typing import Any, Dict, List, Union

from dateutil.parser import parse
from humanize import naturaldelta
from python_graphql_client import GraphqlClient
from requests import HTTPError
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Column, Table

console = Console()

client = GraphqlClient(endpoint="https://api.github.com/graphql")


def gh_graphql_query(query, variables, headers) -> Union[Dict[str, Any], HTTPError]:
    try:
        response = client.execute(
            query=query,
            variables=variables,
            headers=headers,
        )
        return response
    except HTTPError as e:
        return e


def _print_http_error(error: HTTPError):
    console.print(
        "HTTPError occured. If '401 Client Error', "
        "check your [bold]GITHUB_TOKEN[/bold]."
    )
    console.print(error)


def rich_link_string(string: str, url: str) -> str:
    return f"[link={url}]{string}[/link]"


def print_token_error():
    console.print(
        "[red]ERROR:[/red] [bold]GITHUB_TOKEN[/bold] environment variable not found"
    )
    console.print("Run `export GITHUB_TOKEN=<your_token>` and try again.")
    console.print("Or run the command with GITHUB_TOKEN=<your_token> prefixed.")
    console.print(
        "See also:"
        "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
    )


def dt_to_human_duration(dt: datetime):
    return naturaldelta(dt - datetime.now(tz=timezone.utc)) + " ago"


def date_format(dt: datetime) -> str:
    return f"{dt.date()} ({dt_to_human_duration(dt)})"


def no_data_panel(author: str, type: str):
    console.print(
        Panel(
            f"No [bold]{type}[/bold] created from user " f"[#7BC4C4]{author}[/#7BC4C4]",
            expand=False,
        )
    )


def process_issues(issues_data_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues_data = [
        d for d in issues_data_response["data"]["search"]["edges"] if d != {"node": {}}
    ]
    return issues_data


def process_discussions(
    discussions_data_response: Dict[str, Any]
) -> List[Dict[str, Any]]:
    discussions_data = [
        d
        for d in discussions_data_response["data"]["search"]["edges"]
        if d != {"node": {}}
    ]
    return discussions_data


def issues_to_table(issues_data, user: str, limit_title: int = 0):
    table = Table(
        Column(header="Title"),
        "Created",
        "State",
        title=f"[#F0C05A]Issues/PRs[/#F0C05A] Created by "
        f"[#7BC4C4]{user}[/#7BC4C4] (n={len(issues_data)})",
        show_lines=False,
        title_justify="left",
        box=box.SIMPLE,
    )
    for row in issues_data:
        d = row["node"]
        date = parse(d["createdAt"])
        title = d["title"] if limit_title == 0 else shorten(d["title"], limit_title)
        table.add_row(
            rich_link_string(title, d["url"]),
            date_format(date),
            d["state"],
        )
    return table


def discussions_to_table(discussions_data, user: str, limit_title: int = 0):
    table = Table(
        Column(header="Title"),
        "Created",
        "State",
        title=f"[#88B04B]Discussions[/#88B04B] Created by "
        f"[#7BC4C4]{user}[/#7BC4C4] (n={len(discussions_data)})",
        show_lines=False,
        title_justify="left",
        box=box.SIMPLE,
    )
    for row in discussions_data:
        d = row["node"]
        date = parse(d["createdAt"])
        title = d["title"] if limit_title == 0 else shorten(d["title"], limit_title)
        table.add_row(
            rich_link_string(title, d["url"]),
            date_format(date),
            "ANSWERED" if d["answer"] is not None else "UNANSWERED",
        )
    return table


def user_data_to_dict(user_data):
    return next(
        (d["node"] for d in user_data["data"]["search"]["edges"] if d != {"node": {}}),
        None,
    )


def print_user_data(user_data):
    console.print(f"[b]Username[/b]: [#7BC4C4]{user_data['login']}[/#7BC4C4]")
    console.print(f"[b]Name[/b]: {user_data['name']}")
    console.print(f"[b]URL[/b]: [#92A8D1]{user_data['url']}[/#92A8D1]")
    console.print(
        f"[b]Account Created[/b]: [i]{date_format(parse(user_data['createdAt']))}[/i]",
        highlight=False,
    )
    console.print("\n")


def process_issue_comments(
    issue_commenter_response: Dict[str, Any], user: str
) -> List[Dict[str, Any]]:
    data = []
    edges = issue_commenter_response["data"]["search"]["edges"]
    for edge in edges:
        title = edge["node"]["title"]
        for comment in edge["node"]["comments"]["nodes"]:
            if comment["author"]["login"].lower() == user.lower():
                date = comment["createdAt"]
                url = comment["url"]
                state = edge["node"]["state"]
                data.append(dict(title=title, date=date, url=url, state=state))
    data = sorted(data, key=lambda d: d["date"], reverse=True)
    return data


def issue_comments_to_table(issue_comments_data, user: str, limit_title: int = 0):
    table = Table(
        Column(header="Title"),
        "Created",
        "State",
        title=f"[#F0C05A]Comments on Issues[/#F0C05A] from "
        f"[#7BC4C4]{user}[/#7BC4C4] (n={len(issue_comments_data)})",
        show_lines=False,
        title_justify="left",
        box=box.SIMPLE,
    )
    for row in issue_comments_data:
        title = row["title"] if limit_title == 0 else shorten(row["title"], limit_title)
        table.add_row(
            rich_link_string(title, row["url"]),
            date_format(parse(row["date"])),
            row["state"],
        )
    return table


def process_discussion_comments(
    discussion_commenter_response: Dict[str, Any], user: str
) -> List[Dict[str, Any]]:
    data = []
    edges = discussion_commenter_response["data"]["search"]["edges"]
    for edge in edges:
        title = edge["node"]["title"]
        for comment in edge["node"]["comments"]["nodes"]:
            if comment["author"]["login"].lower() == user.lower():
                date = comment["createdAt"]
                url = comment["url"]
                category = (
                    "[green]ANSWER[/green]"
                    if comment["isAnswer"]
                    else "[cyan]SUGGESTED ANSWER[/cyan]"
                )
                data.append(dict(title=title, date=date, url=url, category=category))
            for reply in comment["replies"]["nodes"]:
                if reply["author"]["login"].lower() == user.lower():
                    date = reply["createdAt"]
                    url = reply["url"]
                    category = "COMMENT"
                    data.append(
                        dict(title=title, date=date, url=url, category=category)
                    )
    data = sorted(data, key=lambda d: d["date"], reverse=True)
    return data


def discussion_comments_to_table(
    discussion_comments_data, user: str, limit_title: int = 0
):
    table = Table(
        Column(header="Title"),
        "Created",
        "Category",
        title=f"[#88B04B]Comments on Discussions[/#88B04B] from "
        f"[#7BC4C4]{user}[/#7BC4C4] (n={len(discussion_comments_data)})",
        show_lines=False,
        title_justify="left",
        box=box.SIMPLE,
    )
    for row in discussion_comments_data:
        title = row["title"] if limit_title == 0 else shorten(row["title"], limit_title)
        table.add_row(
            rich_link_string(title, row["url"]),
            date_format(parse(row["date"])),
            row["category"],
        )
    return table
