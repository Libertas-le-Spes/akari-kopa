MERGE_REQUEST = "iid title webUrl createdAt project { fullPath } author { name username } headPipeline { status }"


def discussions(after: str = "") -> str:
    return (
        f"discussions(first: 100{after}) {{ pageInfo {{ hasNextPage endCursor }}"
        f" nodes {{ resolvable resolved notes(first: 1) {{ nodes {{ system createdAt author {{ username bot }} }} }} }} }}"
    )


CONVERSATION = f"project {{ fullPath userPermissions {{ pushCode }} }} {discussions()}"

BOARD = f"""
query {{
  currentUser {{
    username
    authoredMergeRequests(state: opened, sort: CREATED_DESC) {{ nodes {{ {MERGE_REQUEST} {CONVERSATION} }} }}
    reviewRequestedMergeRequests(state: opened, sort: CREATED_DESC) {{ nodes {{ {MERGE_REQUEST} }} }}
  }}
}}"""

MORE_DISCUSSIONS = (
    "query($project: ID!, $iid: String!, $after: String!) { project(fullPath: $project) { mergeRequest(iid: $iid) { "
    + discussions(", after: $after")
    + " } } }"
)
