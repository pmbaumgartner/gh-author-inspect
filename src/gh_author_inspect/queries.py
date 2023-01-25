from pathlib import Path

user_basics_query = Path(
    Path(__file__).parent / "query_templates/user_basic.graphql"
).read_text()
issues_query = Path(
    Path(__file__).parent / "query_templates/issue_author.graphql"
).read_text()
discussions_query = Path(
    Path(__file__).parent / "query_templates/discussion_author.graphql"
).read_text()
issues_comment_query = Path(
    Path(__file__).parent / "query_templates/issue_commenter.graphql"
).read_text()
discussions_comment_query = Path(
    Path(__file__).parent / "query_templates/discussion_commenter.graphql"
).read_text()
