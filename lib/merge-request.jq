def pipeline($passing; $failing):
  [.] | flatten | map(select(. != null)) as $states
  | if any($states[]; IN($failing[])) then "failing"
    elif ($states | length) > 0 and all($states[]; IN($passing[])) then "passing"
    else "pending" end;

def person($name; $login):
  if $name == null or $name == "" then $login else $name end;

def card($role; $passing; $failing):
  { role: $role,
    reference,
    title,
    url,
    project,
    author,
    pipeline: (.status | pipeline($passing; $failing)) };
