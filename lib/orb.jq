def days: . * 86400;
def hold: 3 | days;
def checks: [3, 5, 7, 14, 21, 28] | map(days);
def given_up: 30 | days;

def age($now): $now - (.createdAt | fromdateiso8601);

def held($now): age($now) < hold;

def last_check($now):
  (.createdAt | fromdateiso8601) + (age($now) as $age | checks | map(select(. <= $age)) | max);

def seen_at_last_check($now):
  .waitingSince != null and (.waitingSince | fromdateiso8601) <= last_check($now);

def still_followed($now): age($now) < given_up and (held($now) or seen_at_last_check($now));

def shown($now): (.foreign | not) or still_followed($now);

def settled: { none: "idle", passing: "passing" }[.pipeline];

def waiting_or_settled: if .waitingSince then "comments" else settled end;

def orb: if settled then waiting_or_settled else .pipeline end;

def on_the_bar($now): map(select(shown($now)) | . + { orb: orb });
