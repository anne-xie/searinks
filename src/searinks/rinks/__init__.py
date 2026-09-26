from searinks.models import Rink
from searinks.rinks.kraken import KRAKEN
from searinks.rinks.snoking import SNOKING

RINKS: dict[str, Rink] = {rink.key: rink for rink in [KRAKEN, SNOKING]}
