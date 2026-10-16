from datetime import timedelta

from akari_kopa.attention.repository.repository import OwnRepository, SomeoneElsesRepository

OWN = OwnRepository()

SOMEONE_ELSES = SomeoneElsesRepository(
    hold=timedelta(days=3),
    checks=tuple(timedelta(days=day) for day in (3, 5, 7, 14, 21, 28)),
    let_go=timedelta(days=31),
)

REPOSITORIES = {repository.name: repository for repository in (OWN, SOMEONE_ELSES)}
