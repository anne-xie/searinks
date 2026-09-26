from searinks.models.rink import Rink
from searinks.rinks.kraken import KRAKEN
from searinks.rinks.lynnwood import LYNNWOOD
from searinks.rinks.ova import OVA
from searinks.rinks.snoking import SNOKING

RINKS: dict[str, Rink] = {rink.key: rink for rink in [KRAKEN, SNOKING, OVA, LYNNWOOD]}
