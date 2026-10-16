def pipeline($passing; $failing):
  [.] | flatten | map(select(. != null)) as $states
  | if ($states | length) == 0 then "none"
    elif any($states[]; IN($failing[])) then "failing"
    elif all($states[]; IN($passing[])) then "passing"
    else "pending" end;

def person($name; $login):
  if $name == null or $name == "" then $login else $name end;

def waiting_since($threads; $comments; $answered):
  $threads + [$comments[] | select(. > $answered)] | min;

def card($role; $passing; $failing):
  { role: $role,
    reference,
    title,
    url,
    project,
    author,
    pipeline: (.status | pipeline($passing; $failing)),
    createdAt,
    foreign: (.foreign // false),
    waitingSince };
