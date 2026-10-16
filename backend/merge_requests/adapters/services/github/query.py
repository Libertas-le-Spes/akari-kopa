PULL_REQUEST = (
    "id number title url createdAt repository { nameWithOwner } author { login ... on User { name } }"
    " commits(last: 1) { nodes { commit { committedDate statusCheckRollup { state } } } }"
)

SOMEONE = "author { __typename login }"


def threads(after: str = "") -> str:
    return (
        f"reviewThreads(first: 100{after}) {{ pageInfo {{ hasNextPage endCursor }}"
        f" nodes {{ isResolved comments(first: 1) {{ nodes {{ {SOMEONE} createdAt }} }} }} }}"
    )


BOARD = f"""
query {{
  viewer {{
    login
    pullRequests(states: OPEN, first: 50, orderBy: {{ field: CREATED_AT, direction: DESC }}) {{ nodes {{ {PULL_REQUEST} }} }}
  }}
  search(query: "is:open is:pr review-requested:@me archived:false", type: ISSUE, first: 50) {{ nodes {{ ... on PullRequest {{ {PULL_REQUEST} }} }} }}
}}"""

CONVERSATION = f"""
query($id: ID!) {{
  node(id: $id) {{
    ... on PullRequest {{
      repository {{ viewerPermission }}
      {threads()}
      comments(last: 100) {{ nodes {{ {SOMEONE} createdAt }} }}
      reviews(last: 100) {{ nodes {{ {SOMEONE} state body submittedAt }} }}
    }}
  }}
}}"""

MORE_THREADS = f"query($id: ID!, $after: String!) {{ node(id: $id) {{ ... on PullRequest {{ {threads(', after: $after')} }} }} }}"
