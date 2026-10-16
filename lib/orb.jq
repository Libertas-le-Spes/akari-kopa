def days: . * 86400;
def hold: 3 | days;
def recheck: 2 | days;

def opened: .createdAt | fromdateiso8601;

def held($now): $now - opened < hold;

def last_check($now):
  opened + hold + ((($now - opened - hold) / recheck) | floor) * recheck;

def seen_at_last_check($now):
  .waitingSince != null and (.waitingSince | fromdateiso8601) <= last_check($now);

def shown($now): (.foreign | not) or held($now) or seen_at_last_check($now);

def quiet: if .waitingSince then "comments" else "idle" end;

def orb: if .pipeline == "none" then quiet else .pipeline end;

def on_the_bar($now): map(select(shown($now)) | . + { orb: orb });
