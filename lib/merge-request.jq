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

def epoch:
  if . == null then null else
    capture("^(?<time>[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(\\.[0-9]+)?(?<zone>Z|[+-][0-9]{2}:?[0-9]{2})?$")
    | (.time + "Z" | fromdateiso8601) as $utc
    | (.zone // "Z") as $zone
    | if $zone == "Z" then $utc
      else ((($zone[1:3] | tonumber) * 3600 + ($zone[-2:] | tonumber) * 60)
            * (if $zone[0:1] == "-" then -1 else 1 end)) as $offset
           | $utc - $offset end
  end;

def merged_card($role; $passing; $failing; $now):
  . as $merge_request
  | card($role; $passing; $failing) + { merged: true }
  | select(($merge_request.status != null and .pipeline == "pending")
           or ((($merge_request.settled // $merge_request.mergedAt) | epoch) > $now - 900));
