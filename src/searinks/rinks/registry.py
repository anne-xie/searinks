from searinks.models.rink import Rink
from searinks.rinks.kirkland import KIRKLAND
from searinks.rinks.kraken import KRAKEN
from searinks.rinks.lynnwood import LYNNWOOD
from searinks.rinks.ova import OVA
from searinks.rinks.renton import RENTON
from searinks.rinks.snoqualmie import SNOQUALMIE

RINKS: dict[str, Rink] = {rink.key: rink for rink in [KRAKEN, KIRKLAND, RENTON, SNOQUALMIE, OVA, LYNNWOOD]}
