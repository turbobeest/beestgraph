#!/usr/bin/env python3
"""Generate per-item bucket-list pages and rewrite the parent MOC.

One-shot generator. Writes files under 07-resources/bucket-list/<section>/.
Skips files that already exist (Hang Glide, Style & Wellness items).
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime

VAULT = Path("/home/turbobeest/vault/07-resources/bucket-list")
TODAY = "2026-05-03"
UID_BASE = 20260503140000

ITEMS: list[dict] = []


def add(
    title: str,
    section: str,
    summary: str,
    *bullets: str,
    aliases: list[str] | None = None,
    related: list[str] | None = None,
    status: str = "pending",
    topics_extra: list[str] | None = None,
    tags_extra: list[str] | None = None,
    notes: str | None = None,
):
    ITEMS.append(
        {
            "title": title,
            "section": section,
            "summary": summary,
            "bullets": list(bullets),
            "aliases": aliases or [],
            "related": related or [],
            "status": status,
            "topics_extra": topics_extra or [],
            "tags_extra": tags_extra or [],
            "notes": notes,
        }
    )


# Section ordering for the MOC
SECTION_ORDER = [
    ("adventure", "Adventure"),
    ("exotic-food-drink", "Exotic Food & Drink"),
    ("food-drink-experiences", "Food & Drink Experiences"),
    ("creative", "Creative"),
    ("style-wellness", "Style & Wellness"),
    ("nature-wildlife", "Nature & Wildlife"),
    ("finance-luxury", "Finance & Luxury"),
    ("entertainment", "Entertainment"),
    ("personal-growth", "Personal Growth"),
]

# Default related = parent only; many items below add a topical sibling.
P = "[[Bucket List]] — parent list"


# ============================================================
# ADVENTURE (Hang Glide already written. Abseil merged into Rappel.)
# ============================================================
add("Air Boat Across an Alligator Infested Swamp", "adventure",
    "Bucket-list adventure goal — ride an airboat across an alligator-inhabited swamp.",
    "Done. Date and personal narrative TBD; update completed_date when known.",
    aliases=["airboat-swamp"], status="completed",
    notes="Status set to completed. Fill in completed_date and Why-it's-on-the-list when ready.")

add("Arrive By Seaplane", "adventure",
    "Bucket-list goal — arrive at a destination via seaplane water landing.",
    "Common in Caribbean (St. Barts, Bahamas), Pacific NW (Kenmore Air, Seattle/San Juans), and Maldives.",
    "Often included as a transfer leg on luxury island bookings; can also be booked standalone.",
    aliases=["seaplane-arrival"])

add("Catch a Wave Surfing", "adventure",
    "Bucket-list goal — catch and ride a wave on a surfboard.",
    "Beginner-friendly entry: 2–3 hour group lessons in mellow breaks (Costa Rica, Waikiki, Cocoa Beach FL).",
    "Most beginners catch their first wave by lesson 2; longboards are easier than shortboards.",
    aliases=["surf", "go-surfing"])

add("Dog Sled", "adventure",
    "Bucket-list goal — drive or ride a dog sled team.",
    "Winter destinations: Alaska (Iditarod tour operators), Yukon, Norway, Quebec.",
    "Half-day to multi-day options; some include sleeping in heated cabins between runs.",
    aliases=["dogsled", "mush-dogs"])

add("Eat Fire", "adventure",
    "Bucket-list goal — perform a fire-eating trick.",
    "Learn from a circus arts school or a fire performer; basic technique can be learned in one session.",
    "Significant burn risk — never self-teach from videos.",
    aliases=["fire-eating"])

add("Explore a Cave", "adventure",
    "Bucket-list goal — go caving / spelunking in an undeveloped cave.",
    "Show caves (Mammoth Cave KY, Carlsbad Caverns NM) for a low-effort intro; wild caves via a guided trip with a local grotto.",
    "Wild caves require helmet, headlamp, three light sources, and someone who knows the system.",
    aliases=["caving", "spelunk"])

add("Flip on a Trampoline", "adventure",
    "Bucket-list goal — land a flip on a trampoline.",
    "Indoor trampoline parks (Sky Zone, Urban Air) have foam pits — safest place to learn.",
    "Front flip is the easiest entry; coach-supervised first attempts strongly recommended.",
    aliases=["trampoline-flip"])

add("Flyboarding", "adventure",
    "Bucket-list goal — ride a water-jet-powered flyboard above a lake or ocean.",
    "Resort/beach operators in Caribbean, Mexico, FL Keys offer 30 min lessons + flight ($150–250).",
    "Most riders are airborne and stable within 15 minutes.",
    aliases=["flyboard"])

add("Go Bamboo Rafting", "adventure",
    "Bucket-list goal — float a river on a traditional bamboo raft.",
    "Classic destinations: Rio Grande in Jamaica (poled bamboo rafts), Li River China, Bali.",
    "Half-day guided trips; calm water, no rapids.",
    aliases=["bamboo-raft"])

add("Go Fat Biking", "adventure",
    "Bucket-list goal — ride a fat-tire bike on snow, sand, or rough terrain.",
    "Rentals in winter destinations (Bend OR, Crested Butte CO) and beach towns.",
    "Lower learning curve than mountain biking — wide tires are very forgiving.",
    aliases=["fatbike"])

add("Hold a Shark", "adventure",
    "Bucket-list goal — hold a small live shark.",
    "Aquarium 'shark encounter' programs (Atlantis Bahamas, Georgia Aquarium) let you handle juveniles or nurse sharks.",
    "Some scuba shark dives also include guided handling.",
    aliases=["shark-handling"])

add("Indoor Skydive", "adventure",
    "Bucket-list goal — fly in an indoor vertical wind tunnel.",
    "iFly chain has US locations; $70–100 for two 1-min flights with instructor.",
    "Good prep for actual skydiving — same body position, no fall risk.",
    aliases=["wind-tunnel", "ifly"],
    related=["[[Skydive]]"])

add("Jump Off a Cliff", "adventure",
    "Bucket-list goal — cliff jump into water.",
    "Famous spots: Rick's Cafe (Negril Jamaica, 35 ft), Black Rock (Maui), Havasu Falls AZ.",
    "Always check water depth and conditions; never jump alone.",
    aliases=["cliff-jump", "cliff-diving"])

add("Kite Surf", "adventure",
    "Bucket-list goal — kitesurf on open water.",
    "3-day beginner certification at a kitesurfing school ($600–1200) is the standard entry path.",
    "Top US schools: Kite House (NC Outer Banks), REAL Watersports.",
    aliases=["kitesurfing", "kiteboard"])

add("Navigate a Personal Underwater SUB", "adventure",
    "Bucket-list goal — pilot a personal submarine underwater.",
    "Scuba SUBs at resorts (Bahamas, Cozumel, Maldives) — $300–800 for a 30 min dive.",
    "Larger luxury subs (DeepFlight, Triton) available on yacht charters.",
    aliases=["personal-submarine", "submarine-dive"])

add("Parasail", "adventure",
    "Bucket-list goal — parasail behind a boat.",
    "Standard tourist activity at any beach destination ($60–120 for 10–15 min flight).",
    "Tandem rigs let two people fly together; very low risk and no skill required.",
    aliases=["parasailing"])

add("Play a Game of Paintball", "adventure",
    "Bucket-list goal — play a full paintball match.",
    "Outdoor fields ($30–60 for half-day); rentals included for first-timers.",
    "Welts/bruises are normal; long sleeves, gloves, and the rented mask are non-negotiable.",
    aliases=["paintball"])

add("Police Ride Along", "adventure",
    "Bucket-list goal — ride along on a police patrol shift.",
    "Most US police departments have a public ride-along program — application form, background check, waiver.",
    "Typical 4–8 hour shift; pick urban evening shift for activity, suburban day shift for calm.",
    aliases=["ride-along"])

add("Rappel Down a Waterfall", "adventure",
    "Bucket-list goal — rappel (abseil) down the face of a waterfall.",
    "Canyoneering tours in Costa Rica, Hawaii (Big Island), Utah offer guided waterfall descents ($150–300).",
    "Prior rappelling experience not required — guides handle technical setup.",
    aliases=["abseil-down-a-waterfall", "waterfall-rappel", "canyoneering"])

add("Rappel into a Cave", "adventure",
    "Bucket-list goal — rappel down into a cave system.",
    "Cave Diving Group / NSS-affiliated guides for technical caves; Mexican cenote tours for accessible options.",
    "Belize ATM Cave and Yucatán cenotes are popular intro options.",
    aliases=["cave-rappel"])

add("Ride a Zip Line", "adventure",
    "Bucket-list goal — ride a zip line.",
    "Resort/canopy tours in Costa Rica, Hawaii, Tennessee — $50–120 for multi-line course.",
    "Long single-line records: Toro Verde Puerto Rico (1.5 miles, 95 mph).",
    aliases=["zipline", "zip-line"])

add("Ride ATVs", "adventure",
    "Bucket-list goal — ride an ATV / quad bike.",
    "Guided trail tours at any rural tourist destination ($60–150 for 2 hrs).",
    "Sand dunes (Glamis CA, Oceano), forests, mountains all common.",
    aliases=["quad-bike", "atv"])

add("Ride in a Hot Air Balloon", "adventure",
    "Bucket-list goal — ride in a hot air balloon at sunrise.",
    "Classic destinations: Cappadocia Turkey, Napa Valley CA, Albuquerque NM (October Balloon Fiesta).",
    "Sunrise flights only; ~1 hour aloft + champagne landing tradition. $200–400.",
    aliases=["balloon-ride", "hot-air-balloon"])

add("Ride in a Luge", "adventure",
    "Bucket-list goal — ride a luge sled down an ice track.",
    "Olympic-track public runs at Lake Placid NY, Park City UT, Whistler BC ($100–200 for a single passenger run).",
    "Summer wheeled-luge tracks (Rotorua NZ, Sentosa Singapore) for warm-weather alternative.",
    aliases=["luge-ride"])

add("Sail a Boat", "adventure",
    "Bucket-list goal — sail a boat (as skipper, not passenger).",
    "ASA 101 (Basic Keelboat) certification — 3-day course, $400–700, qualifies you to charter.",
    "Lake/coastal sailing schools available in most regions; Caribbean live-aboard courses combine training with vacation.",
    aliases=["sailing", "skipper-boat"])

add("Scuba Dive", "adventure",
    "Bucket-list goal — scuba dive on open water.",
    "PADI Open Water certification — 4-day course, ~$400–600, includes pool + 4 ocean dives.",
    "Top first-cert destinations: Cozumel, Bonaire, Roatán, Koh Tao.",
    aliases=["scuba", "diving"])

add("Skijoring", "adventure",
    "Bucket-list goal — be pulled on skis by a horse, dog, or vehicle.",
    "Equine skijoring competitions in Whitefish MT, Leadville CO; dog skijoring rentals at Nordic ski resorts.",
    "Cross-country ski skill required; sprint racing format is most accessible spectator entry.",
    aliases=["skijor"])

add("Skydive", "adventure",
    "Bucket-list goal — jump from an airplane with a parachute.",
    "Tandem jump (no training) is the standard entry: $250–350 for 10,000 ft jump with instructor.",
    "Solo certification (AFF) takes ~7 jumps over a few weeks.",
    aliases=["skydiving", "tandem-jump"],
    related=["[[Indoor Skydive]]"])

add("Snowboard", "adventure",
    "Bucket-list goal — snowboard down a mountain.",
    "Lesson + rental day at any ski resort ($150–300); first day is typically frustrating, second day clicks.",
    "Easier learning curve than skiing for athletic people; harder for people who fear falling backward.",
    aliases=["snowboarding"])

add("Swim with Dolphins", "adventure",
    "Bucket-list goal — swim with dolphins.",
    "Wild encounters (Bimini Bahamas, Kaikoura NZ) are ethically preferable to captive swim programs.",
    "Captive programs (Discovery Cove FL, Atlantis Bahamas) are easier to book but controversial.",
    aliases=["dolphin-swim"])

add("Swim with Sharks", "adventure",
    "Bucket-list goal — swim or dive with sharks.",
    "Cage-free reef shark dives (Bahamas, Fiji, Bora Bora); cage diving with great whites (South Africa, Guadalupe MX).",
    "Whale shark snorkeling (Mexico, Australia) is the gentlest entry.",
    aliases=["shark-dive"])

add("Swim with Stingrays", "adventure",
    "Bucket-list goal — swim with stingrays.",
    "Stingray City (Grand Cayman) is the iconic spot — shallow sandbar with habituated rays.",
    "Antigua, Bora Bora, Belize all have similar tours.",
    aliases=["stingray-swim"])

add("Walk a Suspension Bridge", "adventure",
    "Bucket-list goal — walk across a suspension bridge.",
    "Famous: Capilano (Vancouver BC), Carrick-a-Rede (N. Ireland), Trift (Switzerland), Royal Gorge (CO).",
    "Length and height vary widely — Trift is 170m long over a glacier.",
    aliases=["suspension-bridge"])

add("Walk on Hot Coals", "adventure",
    "Bucket-list goal — walk barefoot across hot coals.",
    "Tony Robbins-style firewalking seminars; some yoga retreats and team-building events offer it.",
    "Physically safe when properly conducted — coals are insulators and contact time is brief.",
    aliases=["firewalk"])

add("Whitewater Rafting", "adventure",
    "Bucket-list goal — whitewater raft a river.",
    "Class II–III for first-timers (Lehigh PA, Nantahala NC); Class IV+ requires experience.",
    "Iconic rivers: Colorado (Grand Canyon), Salmon ID, Futaleufú Chile.",
    aliases=["river-rafting", "whitewater"])

add("Wrap a Snake Around My Neck", "adventure",
    "Bucket-list goal — drape a (non-venomous) snake around your neck.",
    "Reptile zoos and exotic pet shows offer photo-op handling sessions.",
    "Pythons and boas are the typical snakes used — heavy but calm.",
    aliases=["snake-handling"])

add("Zorbing", "adventure",
    "Bucket-list goal — roll downhill inside a giant inflatable ball.",
    "Originated in NZ (Rotorua); now available in OR, TN, UK, China.",
    "Wet zorb (with water inside) and harness zorb are the two formats.",
    aliases=["zorb"])


# ============================================================
# EXOTIC FOOD & DRINK
# ============================================================
add("Ahi Poke", "exotic-food-drink",
    "Bucket-list food goal — try ahi (yellowfin tuna) poke.",
    "Hawaiian raw fish dish — cubed tuna, soy, sesame, onions. Authentic at any Hawaiian poke counter.",
    "Mainland chains (Pokeworks etc.) are decent intros but lack the freshness of island versions.",
    aliases=["poke", "tuna-poke"])

add("Alligator", "exotic-food-drink",
    "Bucket-list food goal — eat alligator.",
    "Cajun/Creole staple — fried alligator bites at any NOLA restaurant.",
    "Tastes like a cross between chicken and fish; tail meat is most tender.")

add("Alpaca", "exotic-food-drink",
    "Bucket-list food goal — eat alpaca.",
    "Common in Peru and Bolivia; alpaca steak or anticucho at restaurants in Cusco, Lima, La Paz.",
    "Lean, sweet flavor; comparable to lean beef with notes of game.")

add("Baby Eel", "exotic-food-drink",
    "Bucket-list food goal — eat baby eel (angulas).",
    "Spanish Basque delicacy — sautéed in olive oil with garlic and chili. Genuine angulas now extremely expensive ($1000+/lb).",
    "Most restaurants serve gulas (surimi imitation); ask for the real thing.",
    aliases=["angulas"])

add("Blood Sausage", "exotic-food-drink",
    "Bucket-list food goal — eat blood sausage.",
    "Variants worldwide: black pudding (UK/Ireland), boudin noir (France), morcilla (Spain), blutwurst (Germany).",
    "Iron-rich, savory, slight sweetness from added fillers (oats, rice, onions).",
    aliases=["black-pudding", "morcilla", "boudin-noir"])

add("Bone Marrow", "exotic-food-drink",
    "Bucket-list food goal — eat roasted bone marrow.",
    "Standard at gastropubs and steakhouses — split marrow bones roasted, served with toast and gremolata.",
    "Rich, buttery, umami; a London specialty (St. John restaurant put it on the modern menu).",
    aliases=["marrow"])

add("Cactus", "exotic-food-drink",
    "Bucket-list food goal — eat cactus (nopales).",
    "Mexican cuisine — grilled or sautéed prickly pear cactus pads. Common in tacos, salads, eggs.",
    "Tart, slightly mucilaginous; comparable to green beans with a hint of citrus.",
    aliases=["nopales", "nopal"])

add("Casu Marzu", "exotic-food-drink",
    "Bucket-list food goal — eat casu marzu (Sardinian maggot cheese).",
    "Illegal under EU food safety law; only available informally on Sardinia.",
    "Pecorino fermented past decay by live cheese fly larvae; eaten with the larvae still inside.",
    aliases=["maggot-cheese"])

add("Caviar", "exotic-food-drink",
    "Bucket-list food goal — eat caviar (the noun and 'eat caviar' deduped here).",
    "Beluga, osetra, and sevruga are the classic sturgeon caviars; farmed sturgeon now standard due to wild bans.",
    "Served on mother-of-pearl spoon with blini, crème fraîche, chives. Single-tin tasting at upscale restaurants $50–150.",
    "Affordable entry: trout roe or salmon ikura.",
    aliases=["eat-caviar", "sturgeon-caviar"],
    topics_extra=["food-drink-experiences"])

add("Conch", "exotic-food-drink",
    "Bucket-list food goal — eat conch.",
    "Caribbean staple — conch fritters, conch salad (raw), cracked conch (fried). Bahamas and Florida Keys are the iconic locations.",
    "Chewy when overcooked; freshness is everything.")

add("Dim Sum", "exotic-food-drink",
    "Bucket-list food goal — eat dim sum at a traditional cart-service restaurant.",
    "Best at large Cantonese restaurants in Chinatowns (NYC, SF, Vancouver, Hong Kong).",
    "Order har gow (shrimp dumplings), siu mai, char siu bao, chicken feet, turnip cake.",
    aliases=["dimsum"])

add("Eel", "exotic-food-drink",
    "Bucket-list food goal — eat eel (unagi).",
    "Most accessible: Japanese unagi don (grilled eel over rice with sweet kabayaki sauce).",
    "Smoked eel is a Dutch/UK delicacy; try at a Dutch fish stall or smokehouse.",
    aliases=["unagi"])

add("Elk", "exotic-food-drink",
    "Bucket-list food goal — eat elk.",
    "Available at game-focused restaurants and butchers in mountain US states (CO, MT, WY).",
    "Lean, slightly sweet; treat like a leaner version of beef and avoid overcooking.")

add("Escargot", "exotic-food-drink",
    "Bucket-list food goal — eat escargot.",
    "Classic French preparation: cooked in shells with garlic, parsley, butter. Standard at French bistros.",
    "Tools provided (snail tongs, small fork); texture is mushroom-like.",
    aliases=["snails"])

add("Flowers", "exotic-food-drink",
    "Bucket-list food goal — eat edible flowers.",
    "Common in tasting menus and craft cocktails — nasturtium, pansies, violets, squash blossoms, hibiscus.",
    "Squash blossoms stuffed with ricotta and fried is the most accessible intro.",
    aliases=["edible-flowers"])

add("Foie Gras", "exotic-food-drink",
    "Bucket-list food goal — eat foie gras.",
    "Banned in California, NY (2022, paused), and several countries on welfare grounds; legal elsewhere.",
    "Best preparations: seared foie gras as appetizer, or torchon (cold cured) on toast.",
    aliases=["fattened-liver"])

add("Frog Legs", "exotic-food-drink",
    "Bucket-list food goal — eat frog legs.",
    "French and Cajun staple — sautéed in garlic butter (Provençal) or fried (Cajun).",
    "Texture similar to chicken thigh; standard at French bistros and NOLA restaurants (Antoine's, Galatoire's).")

add("Guinea Pig", "exotic-food-drink",
    "Bucket-list food goal — eat guinea pig (cuy).",
    "Andean delicacy — Peru, Ecuador, Bolivia. Served whole roasted, often with potatoes.",
    "Best in Cusco area; reservations recommended for whole-animal preparations.",
    aliases=["cuy"])

add("Haggis", "exotic-food-drink",
    "Bucket-list food goal — eat haggis.",
    "Scottish national dish — sheep heart, liver, lungs cooked with oats and spices in a stomach lining.",
    "Best on Burns Night (January 25) at any Edinburgh pub; served with neeps and tatties.")

add("Herring", "exotic-food-drink",
    "Bucket-list food goal — eat herring (pickled, fresh, or rollmops).",
    "Dutch street herring (haring) eaten raw with onions, held by tail and lowered into mouth.",
    "Scandinavian pickled herring (sill) at any Swedish smörgåsbord.")

add("Kimchi", "exotic-food-drink",
    "Bucket-list food goal — eat kimchi.",
    "Korean fermented cabbage — every Korean meal includes some. Standard banchan side.",
    "Variants: baechu (napa cabbage), kkakdugi (radish cubes), oi (cucumber).")

add("Liver", "exotic-food-drink",
    "Bucket-list food goal — eat liver.",
    "Pâté is the gentlest entry; chicken liver mousse or duck pâté at French restaurants.",
    "Liver and onions (American diner classic); Italian fegato alla veneziana.")

add("Mochi", "exotic-food-drink",
    "Bucket-list food goal — eat fresh mochi.",
    "Japanese pounded rice cake — fresh is dramatically better than packaged.",
    "Daifuku (filled with red bean or strawberry); ice cream mochi at Japanese groceries.")

add("Octopus", "exotic-food-drink",
    "Bucket-list food goal — eat octopus.",
    "Greek grilled octopus (htapodi sti schara), Spanish pulpo a la gallega, Japanese takoyaki.",
    "Sushi tako (raw) for an entirely different texture experience.")

add("Ostrich", "exotic-food-drink",
    "Bucket-list food goal — eat ostrich.",
    "South African game restaurants serve ostrich steak as standard menu item.",
    "Lean, beef-like; common at game-meat butchers in US (NM, AZ, TX) too.")

add("Rabbit", "exotic-food-drink",
    "Bucket-list food goal — eat rabbit.",
    "European staple — Italian (rabbit ragu, coniglio in umido), French (lapin à la moutarde), Spanish (paella valenciana).",
    "Mild, lean, similar to dark-meat chicken.")

add("Raw Oysters", "exotic-food-drink",
    "Bucket-list food goal — eat raw oysters on the half shell.",
    "Best in cool months (R-months) for safety and flavor.",
    "Iconic spots: Acme Oyster House (NOLA), Grand Central Oyster Bar (NYC), Whitstable (UK).",
    aliases=["oysters-raw"])

add("Reindeer", "exotic-food-drink",
    "Bucket-list food goal — eat reindeer.",
    "Scandinavian dish — Lappish reindeer stew, smoked reindeer carpaccio in Finland and Norway.",
    "Lean, gamey, slightly sweet.")

add("Scrapple", "exotic-food-drink",
    "Bucket-list food goal — eat scrapple.",
    "Pennsylvania Dutch breakfast meat — pork scraps, cornmeal, spices, sliced and pan-fried.",
    "Standard at PA, DE, and southern NJ diners.")

add("Sea Urchin", "exotic-food-drink",
    "Bucket-list food goal — eat sea urchin (uni).",
    "Japanese sushi standard — uni nigiri or uni-don (over rice). Briny, sweet, custard-textured.",
    "Hokkaido uni is the premium grade; California uni now widely available.",
    aliases=["uni"])

add("Sashimi", "exotic-food-drink",
    "Bucket-list food goal — eat sashimi.",
    "Pure raw fish without rice; eat at a quality sushi restaurant for properly aged, knife-cut fish.",
    "Order omakase (chef's choice) for the full experience.")

add("Scorpion", "exotic-food-drink",
    "Bucket-list food goal — eat a (cooked) scorpion.",
    "Beijing/Donghuamen night market street food: skewered fried scorpions.",
    "Crunchy, mild — closer to shrimp than the dramatic appearance suggests.")

add("Snake", "exotic-food-drink",
    "Bucket-list food goal — eat snake.",
    "Common in Vietnam and southern China — snake hot pot, snake whiskey.",
    "Texture similar to fish; small bones throughout.")

add("Sushi", "exotic-food-drink",
    "Bucket-list food goal — eat sushi at a proper sushi restaurant.",
    "Omakase at a respected sushi-ya is the canonical experience — chef serves what's best that day.",
    "US notable: Sushi Saito (NYC), Sushi Yasuda (NYC), Mori (LA).")

add("Tripe", "exotic-food-drink",
    "Bucket-list food goal — eat tripe.",
    "Italian trippa alla Romana, Mexican menudo (hangover soup), French andouillette sausage.",
    "Honeycomb tripe is the best texture for first-timers.")

add("Truffle", "exotic-food-drink",
    "Bucket-list food goal — eat fresh truffle (white or black).",
    "White truffle (Alba, Italy): shaved fresh at table, season Oct–Dec, $200+ for shaving.",
    "Black truffle (Périgord, France): cooked into dishes, more accessible price.",
    aliases=["white-truffle", "black-truffle"])

add("Ugli Fruit", "exotic-food-drink",
    "Bucket-list food goal — eat an ugli fruit.",
    "Jamaican citrus hybrid (tangerine + grapefruit + Seville orange); sweet-tart, less acidic than grapefruit.",
    "Available in winter at specialty grocers (Whole Foods seasonally).")

add("Wild Boar", "exotic-food-drink",
    "Bucket-list food goal — eat wild boar.",
    "Italian cinghiale ragù; Texas/Florida game restaurants serve boar (invasive species, hunted widely).",
    "Stronger flavor than pork, slightly nutty.")

add("Yak", "exotic-food-drink",
    "Bucket-list food goal — eat yak.",
    "Tibetan and Nepalese cuisine — yak burger, yak cheese, butter tea (yak butter).",
    "US: Tibetan/Nepalese restaurants in NYC, Boston, Toronto have it on menu.")


# ============================================================
# FOOD & DRINK EXPERIENCES (87 - 1 Eat Caviar merged = 86)
# ============================================================
S = "food-drink-experiences"

add("Attend a Beer Festival", S,
    "Bucket-list goal — attend a major beer festival.",
    "GABF (Denver, October) is the US flagship; Oktoberfest (Munich, Sept-Oct) is the global icon.",
    "Smaller regional fests in every US state; check craftbeer.com event listings.")

add("Attend a Low Country Boil", S,
    "Bucket-list goal — attend a Lowcountry boil.",
    "Coastal SC/GA tradition — shrimp, andouille, corn, potatoes boiled with Old Bay, dumped on newspaper-lined table.",
    "Best at Charleston/Savannah-area private events or Frogmore-style restaurants.",
    aliases=["frogmore-stew"])

add("Attend a Pig Roast", S,
    "Bucket-list goal — attend a whole-hog pig roast.",
    "Cuban lechón asado (Christmas Eve), Filipino lechon, Hawaiian luau (kalua pig in imu).",
    "Backyard caja china (Cuban roasting box) or commercial pig roast catering for DIY.")

add("Attend a Tea Tasting", S,
    "Bucket-list goal — attend a curated tea tasting.",
    "Specialty tea shops in major cities offer guided flights ($20–60 for 5–8 teas).",
    "Gongfu cha (Chinese ceremonial brewing) or matcha ceremony for traditional formats.")

add("Attend a Winemakers Dinner", S,
    "Bucket-list goal — attend a winemaker's dinner with wine pairings.",
    "Restaurants regularly host visiting winemakers — multi-course menu paired with their wines, vintner present.",
    "$100–250/seat typical; check restaurant event calendars in wine regions.")

add("Bake a Cake for Someone Special", S,
    "Bucket-list goal — bake a cake from scratch for someone.",
    "Tie to a birthday or anniversary for built-in occasion.",
    "Classic safe choice: chocolate layer cake or carrot cake.")

add("Bake a Loaf of Bread", S,
    "Bucket-list goal — bake bread from scratch.",
    "No-knead bread (NYT Mark Bittman recipe) is the easiest entry; sourdough requires a starter.",
    "Dutch oven yields crusty bakery-style loaf at home.")

add("Boil a Lobster", S,
    "Bucket-list goal — boil a live lobster yourself.",
    "Source live from grocery seafood counter or coastal market; humane dispatch debated (freezer first vs straight in).",
    "Standard cook: 12–15 min per 1.5 lb in heavily salted boiling water.")

add("Bottle a Recipe & Sell it", S,
    "Bucket-list goal — bottle a recipe and sell it commercially.",
    "Cottage food laws vary by state — most allow direct-to-consumer sales without commercial kitchen for low-risk items.",
    "Etsy and farmers markets are the typical entry channels.")

add("Catch, Cook & Eat a Fish", S,
    "Bucket-list goal — catch, clean, cook, and eat a fish in the same day.",
    "Easiest paths: trout in a stocked stream, panfish on a lake.",
    "Pan-fry with butter, salt, lemon — minimal preparation.")

add("Cook a Traditional Dish from a Different Culture", S,
    "Bucket-list goal — cook an authentic dish from a culture not your own.",
    "Pick a dish with a clear lineage (mole poblano, ramen, beef bourguignon, biryani).",
    "Use a regional cookbook (not a fusion or 'easy' adaptation) for authenticity.")

add("Cook Christmas Dinner", S,
    "Bucket-list goal — cook the full Christmas dinner.",
    "Standard British/American: roast turkey or beef rib, sides, gravy, dessert.",
    "Plan timing 2 days ahead — turkey takes 4+ hrs, sides need oven coordination.")

add("Cook Every Dish in One Cookbook", S,
    "Bucket-list goal — cook every recipe in a single cookbook.",
    "Inspired by Julie Powell / Julia Child project. Pick a focused cookbook, not a 1000-recipe encyclopedia.",
    "Good targets: Salt Fat Acid Heat, Plenty, The Food Lab.")

add("Cook With a Celebrity Chef", S,
    "Bucket-list goal — cook alongside a celebrity chef.",
    "Charity auctions occasionally include private dinners with chefs; cooking schools sometimes book guest chefs.",
    "Easier path: take a class at a chef-owned restaurant's adjacent school.")

add("Cook With my Partner", S,
    "Bucket-list goal — cook a meal together with your partner.",
    "Couples cooking classes at any community kitchen ($75–150/couple).",
    "DIY: pick a multi-stage recipe (homemade pasta, dim sum) that requires teamwork.")

add("Create a New Ice Cream Flavor", S,
    "Bucket-list goal — invent and make an original ice cream flavor.",
    "Home ice cream maker ($50–200) is the entry point; Cuisinart and KitchenAid attachments work well.",
    "Salt & Straw and Jeni's blogs publish creative-flavor methodology.")

add("Create an Ice Sculpture", S,
    "Bucket-list goal — carve an ice sculpture.",
    "Ice carving classes at culinary schools (CIA, Johnson & Wales) and trade events.",
    "Block of ice + chainsaw + chisels; full-body workout.")

add("Create Food Art", S,
    "Bucket-list goal — make food art (plated as art).",
    "Bento art (kyaraben), fruit/vegetable carving, plated dessert design.",
    "Photograph results; bento and plate-painting tutorials abundant on YouTube.")

add("Create Latte Art", S,
    "Bucket-list goal — pour a latte art design.",
    "Heart is the entry shape; rosetta is the next milestone.",
    "Requires steaming wand (not a Nespresso); home espresso machine ~$300+ to practice.")

add("Create my Own Cocktail", S,
    "Bucket-list goal — invent an original cocktail.",
    "Start from a classic spec (sour, Old Fashioned, Negroni) and substitute ingredients.",
    "Submit to bartender competitions or local bar to put it on a menu.")

add("Create my Own Recipe", S,
    "Bucket-list goal — invent and document an original recipe.",
    "Test 3+ times to lock in measurements and method before sharing.",
    "Publish to a personal blog or food site (Food52 community, Allrecipes).")

add("Create my Signature Dish", S,
    "Bucket-list goal — develop a signature dish you're known for.",
    "Pick something requested at gatherings — that's already a signal.",
    "Refine over many iterations until proportions and method are locked.")

add("Dismember a Chicken", S,
    "Bucket-list goal — break down a whole chicken.",
    "Standard kitchen skill — separate legs, thighs, wings, breasts, save carcass for stock.",
    "Practice yields massive grocery savings vs pre-cut parts.",
    aliases=["butcher-chicken", "break-down-chicken"])

add("Drink a Bottle of Expensive Champagne", S,
    "Bucket-list goal — drink a bottle of high-end champagne.",
    "Tier markers: Krug, Dom Pérignon, Cristal, Salon (vintage).",
    "Restaurant markup is 2–3x retail; buy at a wine shop, bring corkage to a BYOB.")

add("Drink Absinthe", S,
    "Bucket-list goal — drink absinthe properly prepared.",
    "Traditional ritual: louche with cold water dripped over a sugar cube on slotted spoon.",
    "Real absinthe (re-legalized in US 2007) is widely available; thujone effects largely myth.")

add("Drink at a Distillery", S,
    "Bucket-list goal — drink at the distillery where the spirit was made.",
    "Tour + tasting at any major distillery: Kentucky Bourbon Trail, Scotch distilleries, mezcal palenques in Oaxaca.",
    "Distillery-only releases are common rewards for the visit.")

add("Drink at a Dive Bar", S,
    "Bucket-list goal — drink at an iconic dive bar.",
    "Yelp/Eater 'best dive bar' lists by city are reliable.",
    "Cash, no Instagrammable drinks, regulars with stories.")

add("Drink at an Ice Bar", S,
    "Bucket-list goal — drink at an ice bar.",
    "ICEBAR Stockholm (the original), Magic Ice (Norway/Iceland), seasonal pop-ups in NYC, Chicago, London.",
    "Provided parka and gloves; one drink and you're done in 40 min.")

add("Drink Juice from a Fresh Coconut", S,
    "Bucket-list goal — drink coconut water from a freshly opened coconut.",
    "Beach vendors in tropical destinations (Thailand, Caribbean, Mexico) machete-open them.",
    "Vastly fresher than packaged coconut water.")

add("Drink Fresh Milk from the Cow", S,
    "Bucket-list goal — drink raw milk straight from a cow.",
    "Farm visits and agritourism stays offer this; raw milk legal status varies by state.",
    "Body-temperature milk has a different texture and flavor than refrigerated.")

add("Drink Moonshine", S,
    "Bucket-list goal — drink moonshine.",
    "Legal craft moonshine widely available (Ole Smoky, Sugarlands TN); illegal homemade remains in Appalachian tradition.",
    "Flavored versions (apple pie, peach) are easier entry than unaged corn whiskey.")

add("Drink Sake", S,
    "Bucket-list goal — drink sake at a sake bar.",
    "Order junmai daiginjo for the high end; nigori (cloudy) for sweeter intro.",
    "Served warm or chilled depending on grade — chilled for premium grades.")

add("Drink Tea at a Tea House", S,
    "Bucket-list goal — drink tea at a traditional tea house.",
    "Japanese chashitsu (matcha ceremony), Chinese gongfu cha, English afternoon tea at the Ritz.",
    "Each format is a different experience — pick one to start.")

add("Eat Breakfast in Bed", S,
    "Bucket-list goal — eat breakfast in bed.",
    "Trivially easy — schedule one weekend, prep the night before, stay in bed.",
    "Tray + good coffee + something hot is the standard format.")

add("Eat Ethiopian Food With My Hand", S,
    "Bucket-list goal — eat Ethiopian food with hands using injera.",
    "Standard practice — tear injera (sourdough flatbread), scoop stew, eat. No utensils.",
    "DC has the largest Ethiopian community in the US and the best restaurants.")

add("Eat a Meal Cooked by a Celebrity Chef", S,
    "Bucket-list goal — eat a meal cooked personally by a celebrity chef.",
    "Chef's table seating at restaurants where the chef still cooks; chef's residencies and pop-ups.",
    "Don't confuse 'restaurant owned by a celebrity chef' with the chef being there.")

add("Eat a Molecular Gastronomy Dinner", S,
    "Bucket-list goal — eat a molecular gastronomy tasting menu.",
    "Notable: Alinea (Chicago), Tickets (Barcelona), elBulli's spiritual successors.",
    "Multi-hour tasting menu, $300–800/seat, often 20+ courses.")

add("Eat a Raw Diet for a Day", S,
    "Bucket-list goal — eat only raw food for one day.",
    "Fruits, vegetables, raw nuts/seeds, sashimi, ceviche.",
    "Plan ahead — most prepared foods are off-limits.")

add("Eat Alone at a Restaurant", S,
    "Bucket-list goal — eat solo at a sit-down restaurant.",
    "Bar seating is the easiest entry — built for solo diners.",
    "Bring nothing to read; just be present with the food.")

add("Eat an Insect", S,
    "Bucket-list goal — eat an insect.",
    "Mexican chapulines (toasted grasshoppers) at Oaxacan restaurants; Thai street vendors offer fried crickets/silkworms.",
    "US: cricket protein bars and roasted crickets at health food stores for low-stakes entry.")

add("Eat at a Michelin 3-star Restaurant", S,
    "Bucket-list goal — eat at a Michelin 3-star restaurant.",
    "~140 worldwide; book 2–6 months ahead for top tier.",
    "Tasting menu typical, $400–1000/seat. Notable accessibility: Le Bernardin (NYC), Quince (SF).")

add("Eat at a Food Truck", S,
    "Bucket-list goal — eat from a food truck.",
    "Most cities have weekly food truck rallies; Eater lists best by city.",
    "LA, Portland, Austin have the deepest food truck scenes.")

add("Eat at the French Laundry", S,
    "Bucket-list goal — dine at The French Laundry (Yountville CA).",
    "Reservations open 60 days ahead via Tock at 10am PT; sells out in seconds.",
    "$390/seat tasting menu (excl. wine, tax, service); plan 3 hours.")

add("Eat in a Pitch Black Restaurant", S,
    "Bucket-list goal — eat dinner in total darkness.",
    "Dans le Noir (London, Paris), Opaque (LA, SF). Blind/low-vision wait staff guide diners.",
    "Tasting menu format; the goal is sensory recalibration.")

add("Eat Fondue", S,
    "Bucket-list goal — eat traditional cheese or chocolate fondue.",
    "Swiss tradition — Gruyère and Emmental cheese melted with white wine, kirsch.",
    "Notable: Café du Soleil (Geneva), Melting Pot chain in US for accessible intro.")

add("Eat Southern BBQ in the South", S,
    "Bucket-list goal — eat BBQ in the American South.",
    "Four major US styles: Texas (brisket), Memphis (ribs), Carolina (whole hog/vinegar), KC (sauce-forward).",
    "Notable: Franklin Barbecue (Austin), Skylight Inn (Ayden NC), Snow's BBQ (Lexington TX).")

add("Enter Something in a Food Competition", S,
    "Bucket-list goal — enter a dish in a food competition.",
    "County and state fairs accept entries (pies, preserves, BBQ).",
    "Chili cookoffs, BBQ comps (KCBS-sanctioned), and rib contests have entry-level brackets.")

add("Extract Honey from a Bee Hive", S,
    "Bucket-list goal — extract honey from a hive.",
    "Beekeeping clubs and university extension programs run hands-on workshops.",
    "Extract season is summer; honey is centrifuged from frames in an extractor.")

add("Fillet a Fish", S,
    "Bucket-list goal — fillet a fish from whole.",
    "Standard knife technique — flexible fillet knife, cut along spine, around ribs, skin off.",
    "YouTube tutorials abundant; trout is the easiest first fish.")

add("Go Oyster Hunting", S,
    "Bucket-list goal — gather wild oysters from the shore.",
    "Coastal foraging at low tide (state license required in most US states).",
    "Apalachicola FL, Pacific NW (Hood Canal WA), New England oyster flats.")

add("Go to a Vodka Lounge", S,
    "Bucket-list goal — drink at a vodka lounge with extensive vodka selection.",
    "Russian Tea Room (NYC), Pravda (NYC), Russian-themed lounges in major cities.",
    "Vodka flights ($30–60) compare regions and grain sources.")

add("Go Wine Tasting", S,
    "Bucket-list goal — tour a wine region for tasting.",
    "Napa/Sonoma, Willamette OR, Finger Lakes NY, Walla Walla WA in US; Tuscany, Bordeaux, Mendoza globally.",
    "Tasting fees $20–50/winery, often refunded with bottle purchase.")

add("Have a Dinner Party", S,
    "Bucket-list goal — host a multi-course dinner party.",
    "6–10 guests, multi-course menu, plan menu around your strongest skills.",
    "Salt Fat Acid Heat or Six Seasons cookbook for proven party menus.")

add("Have a Progressive Dining Experience", S,
    "Bucket-list goal — do a progressive dinner across multiple homes/restaurants.",
    "Each course at a different location — appetizer at one, main at another, dessert elsewhere.",
    "Common neighborhood/holiday party format.")

add("Have a Wine Collection", S,
    "Bucket-list goal — curate a wine collection.",
    "Entry threshold: ~50 bottles in proper storage (cool, dark, on side).",
    "Track via CellarTracker; mix age-worthy and ready-to-drink.")

add("Host a Cookie Exchange", S,
    "Bucket-list goal — host a holiday cookie exchange.",
    "Standard format: each guest bakes 4–6 dozen of one cookie, takes home variety.",
    "Best held in early December; 6–12 guests is the sweet spot.")

add("Hunt for Wild Mushrooms", S,
    "Bucket-list goal — forage wild mushrooms.",
    "Local mycological society guided forays — vital for safe identification.",
    "Easy starter species: morel, chanterelle, chicken-of-the-woods, hen-of-the-woods.")

add("Learn a Flair Bartending Trick", S,
    "Bucket-list goal — learn a flair bartending move.",
    "Bottle flip, tin toss, garnish flair — Flairco DVDs and YouTube channels.",
    "Practice with empty bottles over carpet; expect breakage.")

add("Learn to Use Chopsticks", S,
    "Bucket-list goal — eat proficiently with chopsticks.",
    "30–60 min of focused practice gets to functional; weeks to fluent.",
    "Practice picking up beans, rice, peanuts.")

add("Leave a 100% Tip for a Server", S,
    "Bucket-list goal — leave a 100% tip on a meal.",
    "Pick a server who's been excellent; cash if possible (no card-processing fees).",
    "Best on a smaller tab so the gesture is generous, not crushing for the math.")

add("Make a Gingerbread House", S,
    "Bucket-list goal — build a gingerbread house from scratch.",
    "Holiday tradition; royal icing as cement, candies as decoration.",
    "Kit version is the trivial entry; from-scratch dough is the bucket-list version.")

add("Make Cheese", S,
    "Bucket-list goal — make cheese from scratch.",
    "Fresh cheese (ricotta, mozzarella) — under 1 hour, simple equipment.",
    "Aged cheeses require specialized molds, controlled environments, weeks of attention.")

add("Make Fresh Pasta", S,
    "Bucket-list goal — make pasta from scratch.",
    "Egg pasta dough → roll → cut. Standard kitchen tools work; pasta machine helps.",
    "Marcella Hazan's recipe is the canonical Italian-American method.")

add("Make Ice Cream", S,
    "Bucket-list goal — make ice cream from scratch.",
    "Custard base (eggs/cream/sugar) churned in ice cream maker.",
    "No-churn condensed milk versions work without equipment.")

add("Make Jam", S,
    "Bucket-list goal — make jam from scratch.",
    "Strawberry, peach, raspberry are the easy starters.",
    "Water bath canning extends shelf life to a year+.")

add("Make Sushi", S,
    "Bucket-list goal — make sushi at home.",
    "Maki rolls (cucumber, salmon) are the entry; nigiri requires sushi rice technique mastery.",
    "Quality fish from a Japanese grocery, not the regular supermarket.")

add("Make Wine", S,
    "Bucket-list goal — make wine from scratch.",
    "Grape juice + yeast + airlock; basic country-wine kits ($50) for first attempts.",
    "Real wine grapes available in fall in wine regions (must orders).")

add("Order from the Secret Menu at In-n-Out", S,
    "Bucket-list goal — order from the In-n-Out secret menu.",
    "Animal Style (mustard-grilled patty, extra sauce, pickles, grilled onions) is the iconic order.",
    "Also: 4x4, Protein Style, Flying Dutchman, Roadkill Fries.",
    aliases=["in-n-out-secret-menu"])

add("Order One of Everything on a Menu", S,
    "Bucket-list goal — order one of every item on a restaurant menu.",
    "Best at a small menu — taqueria, ramen shop, dim sum cart.",
    "Bring friends; otherwise the leftovers pile up fast.")

add("Own a Food Cart", S,
    "Bucket-list goal — own and operate a food cart.",
    "Permits, commissary kitchen rental, vehicle health inspection — significant investment.",
    "Pop-up format (special events, festivals) is lower commitment than full-time.")

add("Own an Award Winning Restaurant", S,
    "Bucket-list goal — own a restaurant that wins industry awards.",
    "Awards to target: James Beard Foundation, Michelin star, regional best-of lists.",
    "Average path: years of operation, distinct point of view, consistent execution.")

add("Partake in a Food Fight", S,
    "Bucket-list goal — participate in an organized food fight.",
    "La Tomatina (Buñol Spain, August) — global tomato-fight festival.",
    "Pillow fights more common in US; food fight events occasionally pop up at festivals.")

add("Partake in Afternoon Tea", S,
    "Bucket-list goal — have proper afternoon tea.",
    "British tradition — finger sandwiches, scones with clotted cream, pastries, tea.",
    "Notable: The Ritz London, Brown's Hotel; US: Plaza NYC, Peninsula Beverly Hills.")

add("Participate in a Private Wine Tasting", S,
    "Bucket-list goal — attend a private (closed-door) wine tasting.",
    "Wine clubs and importers run private tastings with the maker present.",
    "Higher-end than public tastings; often vertical or library wines.")

add("Pick Fruit From the Tree & Make a Pie", S,
    "Bucket-list goal — pick tree fruit and bake a pie with it.",
    "Apple orchards in fall are the most accessible; berry patches in summer.",
    "Standard apple pie recipe; berries need less work.")

add("Recreate a Childhood Recipe", S,
    "Bucket-list goal — recreate a recipe from childhood.",
    "Get the recipe from family if possible; if it died with someone, reverse-engineer from memory.",
    "Tag recipes by occasion (birthdays, holidays) to preserve context.")

add("Recreate a Classic Dish", S,
    "Bucket-list goal — recreate a famous chef's signature dish at home.",
    "Many top chefs publish cookbooks with home-scale versions of restaurant dishes.",
    "Try Thomas Keller's roast chicken, Massimo Bottura's tortellini.")

add("Shuck Oysters", S,
    "Bucket-list goal — shuck oysters yourself.",
    "Oyster knife + glove or folded towel for hand protection.",
    "Hinge-side approach; pop, slide along top shell, sever adductor muscle.")

add("Start an Herb Garden", S,
    "Bucket-list goal — grow your own herbs.",
    "Window box or raised bed; basil, mint, parsley, thyme, rosemary as starters.",
    "Mint is invasive — keep it in its own container.")

add("Stomp Grapes", S,
    "Bucket-list goal — stomp grapes in a vat.",
    "Wine country harvest events (Sept–Oct in Napa/Sonoma); some wineries offer stomping experiences.",
    "Mostly ceremonial — modern winemaking uses presses.")

add("Take a Cooking Class", S,
    "Bucket-list goal — take a hands-on cooking class.",
    "Sur La Table, Williams Sonoma, local culinary schools, Airbnb Experiences.",
    "Pick a cuisine you want to cook regularly, not just sample.")

add("Toss Pizza Dough in the Air", S,
    "Bucket-list goal — toss pizza dough.",
    "Practice with cold, well-rested dough — too warm and it tears.",
    "Pizzaiolo schools and home pizza enthusiasts (Reddit r/Pizza) have good tutorials.")

add("Try Deep-Fried Twinkies", S,
    "Bucket-list goal — eat a deep-fried Twinkie.",
    "State fair food classic; available at fair food trucks and novelty restaurants.",
    "DIY: dip frozen Twinkie in funnel cake batter, fry in oil at 375°F.")

add("Wade in a Cranberry Bog", S,
    "Bucket-list goal — wade in a flooded cranberry bog.",
    "Visit cape Cod or Wisconsin during cranberry harvest (Sept–Oct); some farms offer bog wade experiences.",
    "Cranberries float because of internal air pockets.")

add("Write a Cookbook", S,
    "Bucket-list goal — write a cookbook.",
    "Self-publish via Blurb, Lulu for low-cost personal cookbook; traditional publishing requires agent + proposal.",
    "Photograph every recipe in consistent lighting; recipes need triple-testing.")


# ============================================================
# CREATIVE (40 items, including Act in a Play with dual tag)
# ============================================================
S = "creative"

add("Act in a Play", S,
    "Bucket-list goal — perform a role in a stage play.",
    "Community theater always casting; auditions advertised on local theater websites and Backstage.",
    "One-act festivals are the lowest-commitment entry — single performance, brief rehearsal cycle.",
    aliases=["stage-act"],
    topics_extra=["entertainment"], tags_extra=["entertainment"])

add("Be Published", S,
    "Bucket-list goal — get published.",
    "Literary magazines (Tin House, Paris Review) for short fiction; traditional publishers for books.",
    "Self-publishing via Amazon KDP or Substack reaches publication threshold immediately.")

add("Blow Glass", S,
    "Bucket-list goal — blow your own glass piece.",
    "Glassblowing studios in most cities offer 1-day intro classes ($120–250) — make a paperweight or ornament.",
    "Notable: Corning Museum of Glass (NY), Pilchuck (WA), Penland (NC).")

add("Complete a Cross Stitch Piece", S,
    "Bucket-list goal — finish a cross-stitch piece.",
    "Beginner kits at any craft store ($15–40); aida cloth, embroidery floss, hoop, pattern.",
    "Modern subversive cross-stitch (Subversive Cross Stitch shop) is an entertaining variant.",
    aliases=["cross-stitch"])

add("Complete a \"Paint by Numbers\"", S,
    "Bucket-list goal — finish a paint-by-numbers piece.",
    "Adult kits range from $20 (kids' versions) to $80 (large detailed canvases).",
    "Pop sites: Winnie's Picks, Paint By Numbers Kit.")

add("Create a Bumper Sticker", S,
    "Bucket-list goal — design and print a bumper sticker.",
    "StickerMule and Sticker Robot for one-off prints; $5–20 for a single sticker.",
    "Vinyl is durable; match shape and finish to your design.")

add("Create a Family Logo", S,
    "Bucket-list goal — design a family logo or coat of arms.",
    "Heraldry/coat-of-arms designers online; or modern logo via Canva/Figma.",
    "Use as letterhead, holiday cards, branded gifts.")

add("Create a Family Tree", S,
    "Bucket-list goal — research and build a family tree.",
    "Ancestry.com or FamilySearch (free, LDS-run) for record access.",
    "DNA tests (AncestryDNA, 23andMe) reveal unknown relatives.")

add("Create a Flower Arrangement", S,
    "Bucket-list goal — make a floral arrangement.",
    "Floristry classes at community colleges and flower farms.",
    "Source from farmers markets or grocery for less than $30.")

add("Create a Piece of Art & Sell it", S,
    "Bucket-list goal — sell a piece of art you created.",
    "Etsy, Saatchi Art, local craft fairs.",
    "Pricing: cost of materials + time + 20-50% margin minimum.")

add("Create Personal Stationery", S,
    "Bucket-list goal — design custom personal stationery.",
    "Vistaprint and Minted for printed; Crane & Co for engraved.",
    "Monogrammed letterhead and matching envelopes for a classic set.")

add("Decorate a Blank T-Shirt", S,
    "Bucket-list goal — decorate a blank T-shirt.",
    "Tie-dye, fabric paint, iron-on transfers, embroidery.",
    "Cricut machine enables vinyl cut-and-press for clean designs.")

add("Decoupage Something", S,
    "Bucket-list goal — decoupage an object with paper images and glue.",
    "Mod Podge + magazine cutouts on a wood box, tray, or piece of furniture.",
    "Multiple thin coats; sand between layers.")

add("Design a Website", S,
    "Bucket-list goal — design and launch a website.",
    "Squarespace and Wix for code-free; HTML/CSS for hand-built.",
    "Domain via Namecheap or Cloudflare; pick something memorable.")

add("Enter Art in an Exhibit", S,
    "Bucket-list goal — exhibit art in a public show.",
    "Local art associations, library shows, juried exhibitions, open calls on CaFE (CallForEntry.org).",
    "Coffee shops and breweries often display rotating local art.")

add("Get Handwriting Analyzed", S,
    "Bucket-list goal — get a graphologist to analyze your handwriting.",
    "Professional graphologists offer paid analyses ($50–200); accuracy debated.",
    "Submit a full page of natural writing on unlined paper.")

add("Have Nude Body Artistically Painted", S,
    "Bucket-list goal — sit for nude body painting.",
    "Body painting festivals (World Bodypainting Festival in Austria); private artist commissions.",
    "Several-hour sit; photo documentation typical.")

add("Knit a Scarf", S,
    "Bucket-list goal — knit a scarf from scratch.",
    "Garter stitch (knit every row) on size 9–11 needles, chunky yarn — beginner classic.",
    "Local yarn store classes, YouTube tutorials, Ravelry pattern community.")

add("Make a Calendar with my own Photos", S,
    "Bucket-list goal — make a custom photo calendar.",
    "Shutterfly, Vistaprint, Mixbook ($25–60).",
    "12 strong photos; upload, lay out, ship in a week.")

add("Make a Candle", S,
    "Bucket-list goal — make a candle from scratch.",
    "Soy wax + cotton wick + fragrance + container ($30 kit).",
    "Pour at 135°F; cure 1–2 weeks for best scent throw.")

add("Make a Coloring Book", S,
    "Bucket-list goal — make your own coloring book.",
    "Procreate or Adobe Illustrator for line art; KDP for self-publishing.",
    "Adult coloring market still active — niche themes (botanical, mandala) sell well.")

add("Make a Font Out of My Handwriting", S,
    "Bucket-list goal — turn your handwriting into a usable font.",
    "Calligraphr.com — fill out template by hand, scan, get a TTF/OTF font ($8–25).",
    "iFontMaker on iPad for tablet-drawn fonts.")

add("Make a Handmade Gift", S,
    "Bucket-list goal — make a handmade gift.",
    "Knitting, woodworking, baked goods, art — pick a medium you can practice.",
    "Time investment > monetary cost; recipients value craft.")

add("Make a Handmade Greeting Card", S,
    "Bucket-list goal — make a handmade greeting card.",
    "Watercolor, papercraft, calligraphy, photo collage.",
    "Stamping kits (Stampin' Up!, Hero Arts) for repeatable card making.")

add("Make a Scrapbook", S,
    "Bucket-list goal — make a scrapbook.",
    "Theme by event (wedding, year, trip) for narrative coherence.",
    "Modern alternatives: photo books (Shutterfly), digital scrapbooks (Project Life app).")

add("Make a Tie Dye Shirt", S,
    "Bucket-list goal — tie-dye a shirt.",
    "Spiral, bullseye, crumple are the classic patterns.",
    "Soda ash pre-soak for vivid colors; cure in plastic bag 24 hours before rinsing.")

add("Make an Origami Animal", S,
    "Bucket-list goal — fold an origami animal.",
    "Crane is the gateway; harder: rabbit, dragon, modular origami.",
    "Origami.me and Robert Lang's diagrams for serious models.")

add("Make Mosaic Art", S,
    "Bucket-list goal — make a piece of mosaic art.",
    "Tile + grout + substrate; Pique assiette uses broken china.",
    "Stepping stones and small tabletops are good first projects.")

add("Make Paper", S,
    "Bucket-list goal — make handmade paper.",
    "Pulp recycled scraps in blender; mold and deckle to form sheets; press and dry.",
    "Add seeds, flowers, threads for textured/seed paper.")

add("Make Soap", S,
    "Bucket-list goal — make handmade soap.",
    "Cold process (lye + oils + water) is the traditional method; melt-and-pour for safer entry.",
    "4–6 week cure for cold process; immediately usable for melt-and-pour.")

add("Make Stained Glass", S,
    "Bucket-list goal — make a stained glass piece.",
    "Tiffany method (copper foil) at any stained glass studio; classes $200–500 for first piece.",
    "Suncatcher first project; window panel as the upgrade.")

add("Paint Something at a Ceramic Store", S,
    "Bucket-list goal — paint a ceramic piece at a paint-your-own-pottery studio.",
    "Color Me Mine and similar chains in most US cities; pick bisqueware, paint, return after kiln firing.",
    "$15–50 + piece cost; takes 1 week to fire and pick up.")

add("Refinish a Piece of Furniture", S,
    "Bucket-list goal — refinish a piece of furniture.",
    "Estate sale or thrift find; strip, sand, stain or paint, seal.",
    "Citristrip for chemical strip; orbital sander speeds the prep.")

add("Sew Something You Can Wear", S,
    "Bucket-list goal — sew a wearable garment.",
    "Easiest entries: elastic-waist skirt, simple T-shirt, drawstring pants.",
    "Patterns from Tilly and the Buttons, Closet Core, Grainline Studio.")

add("Start a Blog", S,
    "Bucket-list goal — start a blog.",
    "Substack, Medium, Ghost, WordPress — pick by control vs ease tradeoff.",
    "First 10 posts establish voice; the second 90 build readership.")

add("Take a Painting Class", S,
    "Bucket-list goal — take a structured painting class.",
    "Watercolor for travel-friendly; oil for richness; acrylic for low setup.",
    "Community ed, art schools, Skillshare, MoMA online courses.")

add("Take an Art Class", S,
    "Bucket-list goal — take an art class.",
    "Drawing fundamentals (perspective, value, gesture) is the foundational class.",
    "Local community college or art center; beats apps for honest critique.")

add("Take Pictures in a Photo Booth", S,
    "Bucket-list goal — take pictures in a photo booth.",
    "Mall photo booths increasingly rare; modern booths at weddings, bars, arcades.",
    "Photoautomat (Berlin chain, also NYC) preserves the chemical-print aesthetic.")

add("Work on a Pottery Wheel", S,
    "Bucket-list goal — throw a piece on a pottery wheel.",
    "Studio classes ($150–300 for 4–6 week course); Ghost-style instruction.",
    "Centering the clay is the hard part; throwing comes after.")

add("Wrap a Present Perfectly", S,
    "Bucket-list goal — wrap a present with crisp, professional finish.",
    "Japanese gift-wrapping (furoshiki, perfectly folded paper corners) — YouTube tutorials.",
    "Sharp scissors, double-sided tape, ribbon, square corners.")

add("Write a Letter in Calligraphy", S,
    "Bucket-list goal — write a letter in calligraphy.",
    "Italic and copperplate are the classic Western styles.",
    "Speedball nibs + ink + practice paper; 10 hours practice for legible script.")

add("Write a Song", S,
    "Bucket-list goal — write a complete original song.",
    "Verse-chorus-verse-chorus-bridge-chorus is the standard pop structure.",
    "Record with phone or GarageBand; lyrics + chord chart counts.")


# ============================================================
# NATURE & WILDLIFE (47)
# ============================================================
S = "nature-wildlife"

add("Attend a Rodeo", S,
    "Bucket-list goal — attend a rodeo.",
    "PRCA-sanctioned events: National Finals Rodeo (Las Vegas, December), Houston Livestock Show, Cheyenne Frontier Days.",
    "Smaller local rodeos in any western US town; admission $10–30.")

add("Bathe an Elephant", S,
    "Bucket-list goal — bathe an elephant in a river.",
    "Ethical sanctuaries only — Elephant Nature Park (Chiang Mai Thailand), Boon Lott's Elephant Sanctuary (no riding).",
    "Avoid trekking camps that use bullhooks or chains.")

add("Chase a Tornado", S,
    "Bucket-list goal — go on a storm-chasing tour.",
    "Tour companies operate in Tornado Alley (April–June): Silver Lining Tours, Storm Chasing Adventure Tours.",
    "$2,500–4,000 for a 6–10 day tour; success not guaranteed.")

add("Clamming", S,
    "Bucket-list goal — dig clams from a tidal flat.",
    "Pacific NW (razor clams), New England (steamers, quahogs).",
    "License required; check daily limits and shellfish closures (red tide).")

add("Climb a Volcano", S,
    "Bucket-list goal — climb a volcano.",
    "Easy hikes: Cerro Negro (Nicaragua), Mt. Vesuvius (Italy), Volcán Pacaya (Guatemala).",
    "Hard summits: Cotopaxi (Ecuador), Mt. Rainier (WA), Kilimanjaro (Tanzania).")

add("Climb to the Top of a Tree", S,
    "Bucket-list goal — climb to the top of a tall tree.",
    "Recreational tree climbing (RTC) uses ropes and harness — guides in major US cities.",
    "Notable: Tree Climbing International, redwood climbs in CA.")

add("Compete in a Frog Jumping Contest", S,
    "Bucket-list goal — enter a frog-jumping competition.",
    "Calaveras County Fair (CA, May) — Mark Twain's namesake event; $5 entry, frogs provided.",
    "Smaller frog jumps at Midwest county fairs.")

add("Complete a Horse Jumping Obstacle", S,
    "Bucket-list goal — clear a jump on horseback.",
    "Riding school 4–6 lesson series builds to small crossrail jump.",
    "Cross-country jumping is the next level; show-jumping rings for course riding.")

add("Drive Through a Dust Storm", S,
    "Bucket-list goal — drive through a dust storm (haboob).",
    "Common in AZ, NM, parts of CA Central Valley (June–September).",
    "Pull over and turn off lights if visibility drops below 10 ft (state safety advice).")

add("Feed a Crocodile", S,
    "Bucket-list goal — feed a (controlled) crocodile.",
    "Gator/croc parks: Crocosaurus Cove (Darwin Australia), Crocodile Encounter (Cuero TX).",
    "Always with handler oversight; never wild specimens.")

add("Feed a Koala Bear", S,
    "Bucket-list goal — feed or hold a koala.",
    "Australian wildlife sanctuaries: Lone Pine (Brisbane), Currumbin Wildlife Sanctuary.",
    "Strict handling time limits per koala under welfare regs.")

add("Feed an Ostrich", S,
    "Bucket-list goal — hand-feed an ostrich.",
    "Ostrich farms in TX, AZ, CA; ostrich pellets in your hand, they're aggressive but won't bite.",
    "Notable: OK Corral Ostrich Ranch (Solvang CA), Rooster Cogburn Ostrich Ranch (AZ).")

add("Herd Cattle", S,
    "Bucket-list goal — herd cattle on horseback.",
    "Working dude ranches in Wyoming, Montana, Colorado offer multi-day cattle drive experiences.",
    "Riding skill required; some ranches offer beginner-friendly versions.")

add("Hike Every Trail at a State Park", S,
    "Bucket-list goal — hike every trail in a state park.",
    "Pick a smaller park (~10 trails) for tractable scope.",
    "Track via AllTrails or paper map; many parks issue completion patches.")

add("Hold a Monkey", S,
    "Bucket-list goal — hold a (sanctuary) monkey.",
    "Ethical sanctuaries only — many wildlife encounter sites exploit primates.",
    "Avoid tourist photo-ops with infant monkeys (parent killed).")

add("Hold a Tarantula Size Spider", S,
    "Bucket-list goal — hold a tarantula.",
    "Petting zoos and reptile expos commonly include tarantula handling.",
    "Rose hair and curly hair are docile species used for handling demos.")

add("Horseback Ride on the Beach", S,
    "Bucket-list goal — ride a horse on the beach.",
    "Caribbean (Jamaica, Dominican Republic), Mexico, Outer Banks NC, Half Moon Bay CA.",
    "$80–200 for 1–2 hour beach ride.")

add("Hug a Redwood", S,
    "Bucket-list goal — hug a redwood tree.",
    "Redwood National Park, Muir Woods, Avenue of the Giants — all in northern CA.",
    "Largest specimens require multiple people to wrap around.")

add("Kiss a Sea Lion", S,
    "Bucket-list goal — kiss a sea lion.",
    "Sea Life Park (Hawaii), Six Flags Discovery Kingdom (CA) offer trainer-mediated photo ops.",
    "Trained behavior, not exploitation — but check facility ethics.")

add("Kiss in the Rain", S,
    "Bucket-list goal — kiss someone in the rain.",
    "Plan for warm rain (summer thunderstorm); cold rain ruins it.",
    "Stand still rather than running — that's the cliché shot.")

add("Make a Snowman", S,
    "Bucket-list goal — build a snowman.",
    "Wet packing snow (around 32°F) is essential; powdery cold snow won't stick.",
    "Three-ball classic; carrot nose, coal eyes, branch arms, scarf for tradition.")

add("Milk a Cow", S,
    "Bucket-list goal — milk a cow by hand.",
    "Working dairy farms with agritourism (most US states).",
    "Technique: thumb-and-forefinger top, squeeze downward through fingers in sequence.")

add("Name a Star", S,
    "Bucket-list goal — name a star.",
    "International Star Registry sells naming rights ($55+); not officially recognized by IAU.",
    "Real astronomy alternative: become a citizen scientist via Zooniverse to identify objects.")

add("Relax in a Natural Hot Spring", S,
    "Bucket-list goal — soak in a natural hot spring.",
    "Iconic: Blue Lagoon (Iceland), Pamukkale (Turkey), Hot Springs NP (AR), Strawberry Park (CO).",
    "Wild hot springs (Conundrum CO, Mystic UT) require hiking in.")

add("Release Baby Turtles into the Ocean", S,
    "Bucket-list goal — help release baby sea turtles to the ocean.",
    "Conservation programs in Costa Rica, Mexico (Riviera Maya), Florida, Galápagos.",
    "Hatching season July–November in most spots; tour operators coordinate with researchers.")

add("Ride a Horse Bareback", S,
    "Bucket-list goal — ride a horse bareback (no saddle).",
    "Requires advanced riding seat; not a beginner activity.",
    "Bareback pad as intermediate option for grip.")

add("Ride in a Horse & Carriage", S,
    "Bucket-list goal — ride in a horse-drawn carriage.",
    "Tourist staple in Charleston, NOLA, Savannah, NYC Central Park.",
    "Some destinations now phasing out for animal welfare; Amish country (PA, OH) for working buggies.")

add("Roll in a Huge Pile of Leaves", S,
    "Bucket-list goal — jump into a large pile of fall leaves.",
    "Rake at home in October/November; deciduous suburb yards are the natural setting.",
    "Trivial bucket item — schedule into a fall weekend.")

add("See a Coral Reef", S,
    "Bucket-list goal — snorkel or dive a coral reef.",
    "Great Barrier Reef (Australia), Belize Barrier Reef, Raja Ampat (Indonesia), Bonaire.",
    "Closer: Florida Keys, Hawaii, Cozumel.")

add("See the Salmon Run", S,
    "Bucket-list goal — see a salmon run.",
    "Pacific NW (Olympic NP), Alaska (Brooks Falls — bears + salmon), British Columbia (Adams River sockeye).",
    "August–October timing; check species-specific run schedules.")

add("Shear a Sheep", S,
    "Bucket-list goal — shear a sheep.",
    "Sheep farms with agritourism; shearing schools (e.g., Olds College AB) for serious technique.",
    "Spring shearing season; one sheep takes a skilled shearer 2 minutes.")

add("Shrimping", S,
    "Bucket-list goal — go shrimping.",
    "Cast nets in tidal flats (FL, GA, SC); commercial trawler day-trip experiences in Gulf coast.",
    "License required in most states.")

add("Sleep in a Stable on a Haystack", S,
    "Bucket-list goal — sleep in a barn on a haystack.",
    "Working farms with overnight stays (HipCamp, FarmStay U.S. listings).",
    "Allergies aside, hay is surprisingly comfortable.")

add("Sleep in a Yurt", S,
    "Bucket-list goal — sleep in a yurt.",
    "Glamping option at many state parks (OR, WA, CO have yurt rentals).",
    "Authentic Mongolian gers in Mongolia or Kyrgyzstan for the real experience.")

add("Sleep in an Igloo", S,
    "Bucket-list goal — sleep overnight in an igloo.",
    "Igloo hotels: Kakslauttanen (Finland), Hôtel de Glace (Quebec).",
    "DIY winter camping requires snow saw and 6+ hours to build.")

add("Stand Under a Waterfall", S,
    "Bucket-list goal — stand under a waterfall.",
    "Plunge pools at the base of accessible falls (Havasu, Multnomah, Niagara behind-the-falls tour).",
    "Lighter-flow waterfalls are safest; high-flow waterfalls can knock you down.")

add("Swim in the Ocean", S,
    "Bucket-list goal — swim in the ocean.",
    "Trivial entry — any beach. Bucket list version implies a notable ocean (Indian, Arctic).",
    "Cold water plunge variants: North Sea (Wim Hof tradition), Antarctic polar plunge.")

add("Swim in an Aquarium", S,
    "Bucket-list goal — swim inside an aquarium tank.",
    "Georgia Aquarium offers swim-with-whale-shark program ($240+).",
    "Some aquariums have shark dive certifications too.")

add("Swim with a School of Fish", S,
    "Bucket-list goal — snorkel/dive surrounded by a school of fish.",
    "Sardine run (S. Africa), bait balls in the Caribbean, schools of fish on any healthy reef.",
    "Coral Triangle (Indonesia, Philippines) has the densest fish biomass.")

add("Swim with Manatees", S,
    "Bucket-list goal — swim with manatees.",
    "Crystal River FL is the only legal manatee swim spot in the US (Three Sisters Springs).",
    "Winter season (November–March) when manatees gather in warm springs.")

add("Swim with Sea Turtles", S,
    "Bucket-list goal — swim with sea turtles.",
    "Hawaii (Turtle Bay, Laniakea Beach), Bali, Galápagos, Great Barrier Reef.",
    "Maintain 6 ft distance under most jurisdictions; never touch.")

add("Take a Falconry Class", S,
    "Bucket-list goal — take a falconry class.",
    "British falconry centers (Hawkfield, Hawk Conservancy Trust); US: Master Falconer experiences (NY, CA, NM).",
    "Half-day intro: handle and fly trained raptors. Full apprenticeship is years.")

add("Walk on a Black Sand Beach", S,
    "Bucket-list goal — walk on a black sand beach.",
    "Iceland (Reynisfjara), Hawaii (Punalu'u Big Island), Greece (Santorini Perissa), Tahiti.",
    "Volcanic origin; sand can get extremely hot in direct sun.")

add("Watch a Caterpillar Turn into a Butterfly", S,
    "Bucket-list goal — watch a caterpillar metamorphose into a butterfly.",
    "Butterfly kits (monarch, painted lady) ship live caterpillars; takes ~3 weeks.",
    "Insect Lore is the standard educational supplier.")

add("Watch the Sunrise & Sunset in one Day", S,
    "Bucket-list goal — see both sunrise and sunset in the same day.",
    "Coastal locations make this easy (east-facing morning, west-facing evening).",
    "Equinox dates give equal day/night for symmetry.")

add("Witness a Solar Eclipse", S,
    "Bucket-list goal — witness a total solar eclipse.",
    "Next major US totalities: Aug 12 2026 (Iceland/Spain), Aug 2 2027 (N. Africa), Aug 22 2044 (US).",
    "ISO-certified eclipse glasses required outside totality.")

add("Whale Watching", S,
    "Bucket-list goal — go whale watching.",
    "Pacific NW (Salish Sea, BC/WA — orcas), Hawaii (humpbacks Dec–April), Cape Cod (humpbacks summer).",
    "Land-based watching at Point Reyes CA, Iceland (Húsavík).")


# ============================================================
# FINANCE & LUXURY (32)
# ============================================================
S = "finance-luxury"

add("Be a Leader in my Field", S,
    "Bucket-list aspirational goal — become a recognized leader in your field.",
    "Public visibility (writing, conference speaking) and unique contribution define field leadership.",
    "Long-arc goal — see Why-it's-on-the-list for personal definition.")

add("Be a Member of an Exclusive Club", S,
    "Bucket-list goal — join an exclusive members-only club.",
    "Soho House (creative), Core Club (business), university clubs, country clubs.",
    "Initiation fees $5K–50K + annual dues; sponsorship by current member typically required.")

add("Be a Self-Made Millionaire", S,
    "Bucket-list aspirational goal — reach $1M net worth on your own.",
    "Long-arc; mix of high savings rate and compounding.",
    "Savings rate matters more than income for first $250K; investment returns dominate after.")

add("Blow a lot of Money Gambling", S,
    "Bucket-list goal — gamble a meaningful amount in a single sitting.",
    "Set the loss limit before walking in; treat as entertainment cost, not investment.",
    "High-limit rooms (Bellagio, Wynn) for the experience; baccarat is the highest-stakes table game.")

add("Charter a Yacht", S,
    "Bucket-list goal — charter a yacht for a trip.",
    "Bareboat (you skipper, requires license) vs crewed (with captain/crew).",
    "Caribbean, Mediterranean common; $5K–20K/week bareboat, $25K–250K+ crewed.")

add("Create a Passive Income", S,
    "Bucket-list goal — create a recurring passive income stream.",
    "Investment dividends, rental property, royalties, digital products.",
    "True 'passive' is rare — most require setup work and ongoing maintenance.")

add("Earn 6 Figures Per Year", S,
    "Bucket-list goal — earn $100,000+ per year.",
    "Career-dependent; common in tech, finance, medicine, law, sales.",
    "Cost of living adjustment matters: $100K in SF ≠ $100K in Cleveland.")

add("Find a Career I Love", S,
    "Bucket-list goal — find work you genuinely enjoy.",
    "Iterative — most people find this after 2–4 career pivots.",
    "Cal Newport's 'So Good They Can't Ignore You' argues skill mastery precedes love.")

add("Flip a House", S,
    "Bucket-list goal — buy, renovate, and resell a house at profit.",
    "Distressed property + clear scope of work + resale market analysis.",
    "Capital, time, and tolerance for cost overruns required; YouTube (HGTV-style flips) oversells the ease.")

add("Fly in a Private Jet", S,
    "Bucket-list goal — fly in a private jet.",
    "Charter ($3K–15K/hr depending on jet size), JetSmarter-style empty leg deals, NetJets fractional ownership.",
    "Wheels Up, XO, Magellan Jets are common charter brokers.")

add("Get Paid to Travel", S,
    "Bucket-list goal — get paid to travel.",
    "Paths: travel writing, photographer/videographer, remote work + nomad visa, tour guide.",
    "Income usually less than salaried equivalent; lifestyle currency makes up the difference.")

add("Have 3 Months of Bills in Savings", S,
    "Bucket-list goal — accumulate 3 months of expenses in savings.",
    "Standard emergency fund recommendation; high-yield savings account (Marcus, Ally) for storage.",
    "Calculate from monthly expenses (not income); aim for 3 months minimum, 6+ ideal.")

add("Have a Housecleaner", S,
    "Bucket-list goal — hire a regular housecleaner.",
    "$80–200 per visit; biweekly is the most common cadence.",
    "Vet via referrals (Care.com, Handy, local Facebook groups).")

add("Have a Positive Net Worth", S,
    "Bucket-list goal — reach positive net worth (assets > liabilities).",
    "Calculate via Personal Capital (now Empower), Mint, or spreadsheet.",
    "Pay down high-interest debt first; then build assets.")

add("Have an IRA", S,
    "Bucket-list goal — open and fund an IRA.",
    "Roth IRA ($7,000/yr 2024 limit) tax-free in retirement; traditional IRA tax-deferred.",
    "Open at Fidelity, Schwab, or Vanguard; auto-invest in target-date fund for hands-off.")

add("Have My Own Business Cards", S,
    "Bucket-list goal — have personal business cards.",
    "Moo, Vistaprint for affordable; engraved letterpress (Studio On Fire) for luxury.",
    "100 cards $25–150; design with name + contact + role/website.")

add("Have No Credit Card Debt", S,
    "Bucket-list goal — eliminate all credit card debt.",
    "Avalanche method (highest APR first) is mathematically optimal; snowball (smallest balance first) is psychologically motivating.",
    "Once eliminated, pay full balance monthly to keep interest at $0.")

add("Hire a Personal Shopper", S,
    "Bucket-list goal — work with a personal shopper.",
    "Department stores (Nordstrom, Saks, Bloomingdale's) offer free personal shoppers above spending threshold.",
    "Independent stylists charge $100–500/session.")

add("Make a Career Out of a Hobby", S,
    "Bucket-list goal — turn a hobby into your career.",
    "Hobbyist-to-pro transition: side gigs first, validate income, then quit.",
    "Risk: monetizing the hobby can extinguish the joy.")

add("Have a FICO Credit Score Over 800", S,
    "Bucket-list goal — reach a FICO credit score above 800.",
    "Pay on time always; keep credit utilization under 10%; long credit history.",
    "Free monitoring via Credit Karma, MyFICO, or your card's free score.")

add("Make a Piece of Jewelry", S,
    "Bucket-list goal — make a piece of jewelry.",
    "Beading and wirework are entry levels; metalsmithing requires studio access.",
    "Local jewelry classes; Lapidary Journal Jewelry Artist for techniques.")

add("Make a Will", S,
    "Bucket-list goal — make a legal will.",
    "Online services (LegalZoom, Trust & Will) for simple estates; lawyer for complex estates.",
    "Costs $0–500 depending on path; update after major life events.")

add("Order Room Service", S,
    "Bucket-list goal — order room service.",
    "Standard at any full-service hotel; expect 18–25% service charge + delivery fee.",
    "Best at boutique hotels; chain hotels often phone-it-in.")

add("Own a Successful Business", S,
    "Bucket-list goal — own a profitable business.",
    "Profitable defined as: covers all costs including your salary at market rate.",
    "Most businesses fail; survivorship bias dominates business books.")

add("Own Tiffany Jewelry", S,
    "Bucket-list goal — own a piece from Tiffany & Co.",
    "Entry: silver pieces ($150–500); icon pieces (Elsa Peretti, Paloma Picasso) $200+.",
    "Iconic engagement ring tier $5K–50K+.")

add("Own Investment Real Estate", S,
    "Bucket-list goal — own investment real estate.",
    "Long-term rental, short-term rental (Airbnb), house hack (live in 1 unit of multi-family).",
    "Cash flow vs appreciation strategy; analysis via BiggerPockets calculators.")

add("Play the Stock Market", S,
    "Bucket-list goal — actively trade stocks.",
    "Brokerage account (Schwab, Fidelity, Robinhood); pick a small position size for learning.",
    "Most active traders underperform index funds; this is bucket-list, not retirement strategy.")

add("Sell Something on the Internet", S,
    "Bucket-list goal — sell something online.",
    "eBay (auctions), Etsy (handmade), Facebook Marketplace (local), Amazon (FBA).",
    "Trivial entry — list one item this weekend.")

add("Set Up an Emergency Fund", S,
    "Bucket-list goal — set up an emergency fund.",
    "3–6 months of expenses in a high-yield savings account.",
    "Keep separate from checking to avoid spending it; auto-transfer monthly.")

add("Sleep on Satin Sheets", S,
    "Bucket-list goal — sleep on satin (or silk) sheets.",
    "Mulberry silk: Lilysilk, Cozy Earth ($300–800 set).",
    "Polyester satin: Amazon ($30–80) for the experience without the price.")

add("Stay at an All-Inclusive Resort", S,
    "Bucket-list goal — stay at an all-inclusive resort.",
    "Caribbean (Mexico, DR, Jamaica) standard; Sandals (couples), Beaches (families).",
    "Higher tier: Excellence, Secrets, El Dorado for adults-only luxury.")

add("Start A Business", S,
    "Bucket-list goal — start a business.",
    "LLC formation in your state ($50–500 + annual fees); EIN free from IRS.",
    "Business plan optional for solo; revenue first, then optimize structure.")

add("Stay in a 5-Star Resort", S,
    "Bucket-list goal — stay at a 5-star hotel or resort.",
    "Forbes Travel Guide and Michelin Guide hotel ratings define official 5-star.",
    "Use credit card points (Hyatt, Marriott Bonvoy) for accessible nights.")


# ============================================================
# ENTERTAINMENT (91 raw - Act in a Play in Creative - Dance at Rave merged)
# ============================================================
S = "entertainment"

# 'Act in a Play' lives in Creative
add("Apply to be on a Reality Show", S,
    "Bucket-list goal — apply to be on a reality TV show.",
    "Casting calls posted at Realitywanted.com, individual show casting pages.",
    "Application + video submission; willingness to commit to filming schedule.")

add("Attend a Black Tie Gala", S,
    "Bucket-list goal — attend a black-tie gala.",
    "Charity galas, museum benefits, opera/symphony opening nights.",
    "Tuxedo (men) or gown (women); $200–2000+ ticket including donation.")

add("Attend a Boxing Match", S,
    "Bucket-list goal — attend a live professional boxing match.",
    "Vegas (Caesars Palace, T-Mobile Arena) for big-name fights; local fight nights for entry-level.",
    "Top tickets $500–10K+ for marquee championships.")

add("Attend a Film Premiere", S,
    "Bucket-list goal — attend a film premiere.",
    "Sundance, Cannes, Toronto Film Festivals; LA/NYC red-carpet premieres.",
    "Industry connections or festival passes (Sundance pass ~$3K) for access.")

add("Attend a Foam Party", S,
    "Bucket-list goal — attend a foam party.",
    "Ibiza nightclubs (Amnesia, Ushuaïa) for the canonical version; Florida and Vegas pool parties for accessible.",
    "Wear minimal clothes you don't mind getting wet; foam carries fragrance/dye.")

add("Attend a Gallery Opening", S,
    "Bucket-list goal — attend an art gallery opening.",
    "First Thursdays / First Fridays art walks in most cities are free public openings.",
    "Major galleries (Gagosian, Pace) have invite-only openings; sign up for mailing lists.")

add("Attend a Gay Pride Event", S,
    "Bucket-list goal — attend a Pride event.",
    "Major US Prides (NYC, SF, LA, Chicago) — late June Pride Month.",
    "Pride parade + festival format standard; many corporate-floats vs grassroots tradeoffs.")

add("Attend a Jazz Festival", S,
    "Bucket-list goal — attend a jazz festival.",
    "Notable: Newport Jazz Festival (RI, August), Monterey Jazz Festival (CA, Sept), New Orleans JazzFest (April–May).",
    "Smaller fests in most cities; check JazzTimes festival calendar.")

add("Attend a Masquerade", S,
    "Bucket-list goal — attend a masquerade ball.",
    "Venice Carnival (February), New Year's Eve masquerades, Mardi Gras Krewe balls (NOLA).",
    "Mask + formal attire required; rentals at costume shops.")

add("Attend a Murder Mystery Dinner", S,
    "Bucket-list goal — attend a murder mystery dinner.",
    "Theater-restaurant chains (Mystery Cafe, Spellbound) and traveling productions.",
    "DIY kits (Hunt a Killer, masterofmystery.com) for home parties.")

add("Attend a Music Festival", S,
    "Bucket-list goal — attend a major music festival.",
    "US: Coachella (CA), Bonnaroo (TN), Lollapalooza (Chicago), Glastonbury (UK).",
    "$300–800 ticket + camping/lodging + food = $1500+ full experience.")

add("Attend a Native American Pow Wow", S,
    "Bucket-list goal — attend a Native American pow wow.",
    "Gathering of Nations (Albuquerque, April) is the largest in N. America.",
    "Many tribal pow wows open to public; respectful behavior expected (no recording sacred dances).")

add("Attend a Poetry Reading", S,
    "Bucket-list goal — attend a live poetry reading.",
    "Local bookstores, university English departments, slam poetry venues.",
    "Slam poetry (Nuyorican Poets Cafe NYC) for high-energy variant.")

add("Attend a Wedding in a Different Country", S,
    "Bucket-list goal — attend a wedding in a country you've never visited.",
    "Destination weddings (Italy, Greece, Mexico) are easy entries.",
    "Cultural weddings (Indian, Nigerian, Japanese) for full traditional experience.")

add("Attend a White Party", S,
    "Bucket-list goal — attend a white party (everyone in white).",
    "Diddy's White Parties (Hamptons), Le Diner en Blanc (international pop-up), Miami Winter Music Conference.",
    "All-white attire required; pricier wines and champagne at most events.")

add("Attend a WWE Match", S,
    "Bucket-list goal — attend a live WWE event.",
    "Monthly PPV events (WrestleMania, Royal Rumble, SummerSlam) and weekly Raw/SmackDown tapings.",
    "Tickets $30 (nosebleeds) to $500+ (ringside).")

add("Be a Game Show Contestant", S,
    "Bucket-list goal — appear as a game show contestant.",
    "Apply via show websites (Wheel of Fortune, Jeopardy!, Price Is Right).",
    "Jeopardy! requires online test pass + audition; Price Is Right is line-up game day.")

add("Be a Member of a TV Studio Audience", S,
    "Bucket-list goal — sit in a live TV studio audience.",
    "Free tickets via 1iota.com (Kimmel, Tonight Show, etc.).",
    "LA and NYC are the studio capitals; book months in advance.")

add("Be an Extra in a Movie", S,
    "Bucket-list goal — be an extra in a film or TV show.",
    "Sign with Central Casting (LA/NY/ATL); attend open extra calls posted on Backstage.",
    "Background work pays $100–200/day for non-union; long days, lots of waiting.")

add("Be in a Commercial", S,
    "Bucket-list goal — appear in a commercial.",
    "Casting websites (Backstage, Casting Networks); local commercial agencies.",
    "Headshots required; SAG-AFTRA membership unlocks higher-paying union work.")

add("Be on a Radio Show", S,
    "Bucket-list goal — appear on a radio show.",
    "Pitch yourself as a guest expert (HARO/Help A Reporter Out for journalist queries).",
    "Podcasts now the dominant entry — pitch to relevant shows in your domain.")

add("Be on a TV Show", S,
    "Bucket-list goal — appear on a TV show.",
    "Reality TV (lower bar), morning show interviews (need a story), local news.",
    "Pitch via show producers or PR firms.")

add("Be on the Cover of a Magazine", S,
    "Bucket-list goal — appear on a magazine cover.",
    "Trade publications and local lifestyle magazines for accessible entry.",
    "Major covers require fame, achievement, or a strategically placed PR firm.")

add("Be a Street Performer", S,
    "Bucket-list goal — perform on the street for tips.",
    "Permits required in most cities; busking-friendly cities: NYC subway (MUNY auditions), New Orleans, Austin.",
    "Acoustic guitar, magic, juggling, painting are common busker formats.")

add("Bet at the Dog Races", S,
    "Bucket-list goal — bet at greyhound dog races.",
    "Greyhound racing now banned in most US states (FL ended 2020); West Virginia and Iowa remain.",
    "International: Macau, Vietnam, UK, Australia.")

add("Bicycle Across the Golden Gate", S,
    "Bucket-list goal — bike across the Golden Gate Bridge.",
    "Bike rental shops near Fisherman's Wharf; ride to Sausalito, ferry back.",
    "Half-day ride; pedestrian/bike lanes well-marked.")

add("Buy the Best Seat in the House", S,
    "Bucket-list goal — buy front-row/best seats to a major event.",
    "Sports: courtside NBA, behind-plate MLB. Concerts: front row pit. Theater: orchestra center.",
    "$500–10K+ depending on event; secondary market (StubHub) for harder-to-find premiums.")

add("Close the Club", S,
    "Bucket-list goal — stay at a nightclub until closing time.",
    "European cities (Berlin, Madrid) where clubs run until sunrise are the canonical version.",
    "Watershed moment is dance-floor at 4am, not just buying a closing-time drink.")

add("Crowd Surf", S,
    "Bucket-list goal — crowd surf at a concert.",
    "Punk, metal, EDM shows are the most accommodating; mosh pit edge is the launch point.",
    "Stage diving (Warped Tour-style) for the harder version.")

add("Dance on a Bar", S,
    "Bucket-list goal — dance on a bar top.",
    "Coyote Ugly bars (chain), bachelorette-friendly venues (Dirty Dancing-style).",
    "Many bars prohibit it for liability — read the room.")

add("Do a Body Shot", S,
    "Bucket-list goal — do a body shot.",
    "Tequila shot from a body part; classic spring break / bachelor party staple.",
    "Lime in mouth, salt on neck/shoulder, shot in between.")

add("Do the Hula", S,
    "Bucket-list goal — perform a hula dance.",
    "Hula classes at Hawaiian cultural centers; luau participation events.",
    "Hula auana (modern, with ukulele) more accessible than hula kahiko (ancient/sacred).")

add("Fly on a Trapeze", S,
    "Bucket-list goal — fly on a trapeze.",
    "Trapeze schools (TSNY in NYC/LA/Chicago, Aerial Arts Academy) offer 1-class intros ($60–80).",
    "Most students hit a basic catch in their first class.")

add("Get a Caricature Drawing", S,
    "Bucket-list goal — get a caricature portrait.",
    "Tourist destinations (boardwalks, theme parks) and Renaissance fairs.",
    "$15–50 for sit; takes 5–15 min.")

add("Get Comped or Upgraded Something", S,
    "Bucket-list goal — get a free upgrade or comp.",
    "Hotel: ask politely at check-in, mention occasion, loyalty status helps.",
    "Casinos comp regulars; airlines occasionally upgrade for status holders.")

add("Get Hypnotized", S,
    "Bucket-list goal — get hypnotized.",
    "Stage hypnosis shows (comedy, audience volunteer); clinical hypnotherapy for genuine session.",
    "Suggestibility varies; not everyone goes under.")

add("Get Swag", S,
    "Bucket-list goal — get free promotional swag.",
    "Conferences, product launches, sample sales, trade shows.",
    "Tech conferences (CES, SXSW) notorious for branded merch.")

add("Get VIP Passes to a Show", S,
    "Bucket-list goal — get VIP passes to a concert or event.",
    "Artist VIP packages (meet & greet, soundcheck access) sold via official channels.",
    "$150–2000+ depending on artist tier.")

add("Go on a Cruise", S,
    "Bucket-list goal — take a cruise.",
    "Caribbean (NCL, Royal Caribbean) most accessible; expedition cruises (Antarctica, Galápagos) for serious bucket entries.",
    "Inside cabins from $400/week; balcony from $800; suites $2500+.")

add("Go to a Blues Bar", S,
    "Bucket-list goal — visit a Blues bar with live music.",
    "Chicago: Buddy Guy's Legends, Kingston Mines. Memphis: Beale Street.",
    "Mississippi Delta blues highway (Hwy 61) for pilgrimage.")

add("Go to a Book Signing", S,
    "Bucket-list goal — attend a book signing.",
    "Independent bookstores host author events constantly; major releases tour at Barnes & Noble.",
    "Pre-buy book at the host store; queue forms early for popular authors.")

add("Go to a Miniature Museum", S,
    "Bucket-list goal — visit a miniature museum.",
    "Mini Museum of Miniatures (Bend OR), Museum of Miniature Houses (Carmel IN), Lilliput Land (Sao Paulo).",
    "Dollhouse exhibits and model railway museums adjacent variants.")

add("Go to a Roller Derby", S,
    "Bucket-list goal — attend a roller derby bout.",
    "Women's Flat Track Derby Association (WFTDA) bouts in most US cities.",
    "$10–25 admission; bring earplugs.")

add("Go to a Toga Party", S,
    "Bucket-list goal — attend a toga party.",
    "College Greek life, themed parties, Mediterranean-themed events.",
    "DIY toga from a flat sheet; YouTube tutorial.")

add("Go to Dinner Theater", S,
    "Bucket-list goal — attend dinner theater.",
    "Medieval Times (multi-city US), Tony 'n' Tina's Wedding (NYC immersive), Murder mystery dinners.",
    "$60–120 typical for dinner + show combo.")

add("Go to a Drive-In Movie", S,
    "Bucket-list goal — see a movie at a drive-in theater.",
    "~300 drive-ins remaining in US; check Drive-Ins.com for nearest.",
    "Bring blankets, snacks, FM radio in car.")

add("Go to a Rave", S,
    "Bucket-list goal — attend a rave.",
    "Major: EDC (Las Vegas), Tomorrowland (Belgium), Ultra (Miami).",
    "Underground warehouse parties for the original spirit; check r/aves for city scenes.",
    aliases=["dance-at-a-rave", "rave"])

add("Go to an Indycar Race", S,
    "Bucket-list goal — attend an IndyCar race.",
    "Indianapolis 500 (May) is the iconic event; smaller IndyCar Series races throughout summer.",
    "Pit road passes for behind-the-scenes access.")

add("Go to NASCAR", S,
    "Bucket-list goal — attend a NASCAR race.",
    "Daytona 500 (February), Talladega, Bristol Night Race are signature events.",
    "Earplugs essential; bring a portable scanner to hear team radios.")

add("Go to a Paint Party", S,
    "Bucket-list goal — attend a paint party.",
    "Sip & paint chains (Painting with a Twist, Pinot's Palette) for the wholesome version.",
    "Glow-in-the-dark/UV paint parties at nightclubs for the wilder variant.")

add("Go to a Renaissance Festival", S,
    "Bucket-list goal — attend a Renaissance festival.",
    "Most US states have one; Bristol Renaissance Faire (WI), TX Renaissance Festival, Sterling NY Renfaire are notable.",
    "Period-themed costume optional but encouraged.")

add("Go to a Tattoo Festival", S,
    "Bucket-list goal — attend a tattoo convention.",
    "Notable: London Tattoo Convention, NYC Empire State Tattoo Expo, Hell City (Phoenix).",
    "Get tattooed on-site or shop for design ideas; many master artists in one place.")

add("Go to ComicCon", S,
    "Bucket-list goal — attend a Comic-Con.",
    "San Diego Comic-Con (July) is the flagship; NY Comic Con, Dragon Con also major.",
    "SDCC tickets sell out instantly; cosplay strongly encouraged.",
    aliases=["comic-con", "sdcc"])

add("Go to the Movies by Myself", S,
    "Bucket-list goal — see a movie alone.",
    "Trivial entry — pick a film, buy one ticket, go. Daytime weekday theaters are emptiest.",
    "Some find it liberating; underrated solo activity.")

add("Have 15 Minutes of Fame", S,
    "Bucket-list goal — have a brief moment of public fame.",
    "Viral video, news interview, public award, news-of-the-weird story.",
    "Andy Warhol's quote — nearly impossible to plan, but recognize when it happens.")

add("Be in the Newspaper", S,
    "Bucket-list goal — be featured in a newspaper.",
    "Letter to the editor (low bar), story pitch to local reporters, accomplishment-based feature.",
    "Local papers eager for community stories.")

add("Host a Game Night", S,
    "Bucket-list goal — host a game night.",
    "Board games (Catan, Codenames), party games (Cards Against Humanity), trivia.",
    "6–10 guests is the sweet spot; multiple games for different group sizes.")

add("Host a Radio Show", S,
    "Bucket-list goal — host a radio show.",
    "Community radio (LPFM, college radio, Internet radio) — many take volunteer hosts.",
    "Podcast as the modern equivalent — totally accessible, no station required.")

add("Join a Flash Mob", S,
    "Bucket-list goal — participate in a flash mob.",
    "Flash mob organizing groups (ImprovEverywhere, local meetup groups).",
    "Choreographed dance most common; rehearsals 1–3 sessions.")

add("Learn a Line Dance", S,
    "Bucket-list goal — learn a line dance.",
    "Country bars offer free lessons; classics: Electric Slide, Cupid Shuffle, Cotton Eye Joe.",
    "YouTube tutorials sufficient for basics.")

add("Learn How to Sing Within my Octave", S,
    "Bucket-list goal — learn vocal range and sing within it.",
    "Voice lessons identify range; sing songs in your key, transpose if needed.",
    "Karaoke practice; pick songs by singers with similar voice type.")

add("Make a Great Toast", S,
    "Bucket-list goal — give a memorable toast.",
    "Structure: greeting, story, sentiment, call to drink. Under 3 minutes.",
    "Specific anecdote > generic praise; rehearse out loud.")

add("Make a House of Cards", S,
    "Bucket-list goal — build a house of cards.",
    "New deck, smooth surface, no airflow. Triangle/lean-to structures most stable.",
    "World records reach 100+ stories; one-story tower is a tractable bucket goal.")

add("Master a Video Game", S,
    "Bucket-list goal — master a video game (top tier of competition or story).",
    "Speedrun, achievement completion, ranked competitive top percentile.",
    "Pick a game you genuinely enjoy — 100s of hours required.")

add("Party in a Private Booth at a Nightclub", S,
    "Bucket-list goal — get a private booth (table service) at a nightclub.",
    "Bottle service minimum spend $500–10K depending on club tier and night.",
    "Vegas (Marquee, Hakkasan), NYC (1OAK, Marquee), Miami (LIV) are the marquee venues.")

add("Perform a Magic Trick", S,
    "Bucket-list goal — learn and perform a magic trick.",
    "Card tricks (cull, double lift) are the foundational skill set.",
    "Penguin Magic and Theory11 for tutorials.")

add("Play a Pinball Machine", S,
    "Bucket-list goal — play pinball.",
    "Pinball arcades (Logan Hardware Chicago, Modern Pinball NYC) and barcades.",
    "Pinball Map app finds nearest machines.")

add("Play a Song on a Harmonica", S,
    "Bucket-list goal — play a recognizable song on harmonica.",
    "C major diatonic harmonica is the entry instrument ($30).",
    "Folk songs (Oh Susanna, Camptown Races) playable in week one.")

add("Play Bingo at a Bingo Hall", S,
    "Bucket-list goal — play bingo at a bingo hall.",
    "Most cities have church-run or VFW bingo nights ($5–20 buy-in).",
    "Larger commercial halls in casinos (Foxwoods, Mohegan Sun).")

add("Pose with a Figure at a Wax Museum", S,
    "Bucket-list goal — pose with a wax figure at Madame Tussauds or similar.",
    "Locations: NYC, LA, Las Vegas, Hollywood, London, Berlin, etc.",
    "$30–45 admission; most allow photography.")

add("Read the Book Before the Movie", S,
    "Bucket-list goal — read a book before its film adaptation releases.",
    "Watch upcoming-film calendars; read before seeing.",
    "Rabbit hole: keep this as a regular practice, not a one-off.")

add("Receive a Fan Letter", S,
    "Bucket-list goal — receive a genuine fan letter from a stranger.",
    "Public-facing creative work (writing, art, music, podcast) generates fan mail eventually.",
    "Hard to engineer — make work that connects with people, then wait.")

add("Record a Song", S,
    "Bucket-list goal — record a song.",
    "Home recording: GarageBand, Audacity. Studio: $50–200/hour for mid-tier studios.",
    "DistroKid distributes to streaming services for $20/year.")

add("Ride a Mechanical Bull", S,
    "Bucket-list goal — ride a mechanical bull.",
    "Country bars (Saddle Ranch chain), state fairs, novelty venues.",
    "Lean back, grip with thighs, free hand up — they'll usually buck you off in 30 sec.")

add("Ride on a Ferris Wheel", S,
    "Bucket-list goal — ride a ferris wheel.",
    "Tallest: London Eye (135m), High Roller (Vegas, 167m), Ain Dubai (250m).",
    "Standard fairs, amusement parks, boardwalks for accessible options.")

add("See a 3-D Movie", S,
    "Bucket-list goal — see a 3D film in theater.",
    "IMAX 3D superior to standard RealD; Avatar: Way of Water set the modern standard.",
    "Glasses provided; classic 3D animation films work best.")

add("See a Ballet", S,
    "Bucket-list goal — see a live ballet.",
    "Classics: Swan Lake, Nutcracker (December staple), Sleeping Beauty, Giselle.",
    "Major US: NYC Ballet, ABT, San Francisco Ballet. Bolshoi/Mariinsky for Russian tradition.")

add("See a Broadway Play", S,
    "Bucket-list goal — see a Broadway show.",
    "TKTS booth (Times Square) for same-day discounts; lottery seats (Hamilton, others) for $10.",
    "Broadway: midtown Manhattan only; West End (London) for British equivalent.")

add("See a Cirque du Soleil Show", S,
    "Bucket-list goal — see a Cirque du Soleil show.",
    "Resident Vegas shows (O at Bellagio, KÀ at MGM, Mystère at TI); touring tent shows.",
    "$60–200 typical; book ahead for top viewing.")

add("See a Foreign Film", S,
    "Bucket-list goal — see a foreign-language film.",
    "Arthouse theaters (Landmark, Alamo Drafthouse), Criterion Channel streaming.",
    "Classics by Kurosawa, Bergman, Truffaut for foundational viewing.")

add("See a Las Vegas Show", S,
    "Bucket-list goal — see a Las Vegas show.",
    "Cirque du Soleil shows, residencies (Adele, Bruno Mars), magic (Penn & Teller).",
    "$50–500+; book through resort or Vegas.com.")

add("See a TED Talk Live", S,
    "Bucket-list goal — see a TED talk live.",
    "Main TED conference in Vancouver (April) very expensive ($10K+); TEDx events local and free.",
    "TEDxYouth and TEDxWomen events also accessible.")

add("See the Tour de France", S,
    "Bucket-list goal — see the Tour de France in person.",
    "Held July annually; mountain stages (Alps, Pyrenees) most spectator-friendly.",
    "Free roadside viewing; tour packages with VIP access $3K–10K.")

add("See a Wimbledon Match Live", S,
    "Bucket-list goal — see a match at Wimbledon.",
    "Public ballot (lottery, deadline December), debenture seats (resold), queue (in-person, 4am for grounds).",
    "All England Club, late June–early July.")

add("See an Opera", S,
    "Bucket-list goal — see a live opera.",
    "First opera: La Bohème, La Traviata, Carmen, Madame Butterfly (most accessible).",
    "Met Opera (NYC) for US gold standard; La Scala (Milan), Royal Opera House (London) globally.")

add("Win a Stuffed Animal at a Carnival", S,
    "Bucket-list goal — win a stuffed animal at a carnival game.",
    "Easier games (water gun race, basketball if rims aren't oversized) vs rigged ones (basketball with shrunk rims, milk bottles).",
    "Trivial bucket entry for any state fair visit.")

add("Win an Award", S,
    "Bucket-list goal — win an award.",
    "Industry-specific recognition; community/local awards more accessible than national.",
    "Even small awards (employee of the month, club recognition) qualify if user wants to count them.")

add("Win Something", S,
    "Bucket-list goal — win something via contest, raffle, or sweepstakes.",
    "Local raffles, social media giveaways, in-store contests.",
    "Genuinely random; persistence over many entries pays off.")

add("Write Your Name in Wet Cement", S,
    "Bucket-list goal — write your name in wet cement.",
    "DIY pour at home (sidewalk repair, driveway patch).",
    "Public sidewalk version typically illegal — vandalism risk.")


# ============================================================
# PERSONAL GROWTH (74)
# ============================================================
S = "personal-growth"

add("Ask My Spouse 20 Questions", S,
    "Bucket-list goal — ask your partner 20 deep questions.",
    "NYT '36 Questions That Lead to Love' (Aron) is the canonical list.",
    "Allow 90 min; alternate questions and full responses.")

add("Attend a Random Free Seminar", S,
    "Bucket-list goal — attend a random free educational seminar.",
    "Eventbrite + 'free' filter; library and university public lectures.",
    "Pick something outside your field for surprise value.")

add("Be a Guest Speaker", S,
    "Bucket-list goal — be a guest speaker at an event.",
    "School career days, professional associations, podcast guest appearances.",
    "Pitch yourself with a clear topic and audience benefit.")

add("Be a Mentor", S,
    "Bucket-list goal — be a mentor to someone.",
    "Big Brothers Big Sisters, professional mentorship programs, informal in-field guidance.",
    "Monthly meetings minimum; multi-year commitment standard.")

add("Be an Organ Donor on my License", S,
    "Bucket-list goal — register as an organ donor.",
    "Trivial — check the box at next DMV visit, or register at organdonor.gov.",
    "About 60% of US adults registered; 17 die daily waiting for transplants.")

add("Be Present at a Birth", S,
    "Bucket-list goal — be present at a birth.",
    "Family member's birth (with permission), or doula/midwifery training.",
    "Birth photography also gets you in the room professionally.")

add("Build a House With Habitat for Humanity", S,
    "Bucket-list goal — build a house with Habitat for Humanity.",
    "Volunteer days at local builds; one-week 'blitz builds'; international Global Village trips.",
    "No skills required for entry-level volunteering.")

add("Do 100 Hours of Volunteer Work", S,
    "Bucket-list goal — log 100 hours of volunteer work.",
    "VolunteerMatch.org for opportunity discovery; track via spreadsheet or app.",
    "100 hours = ~2 hrs/week for a year, or week-long service trip.")

add("Do 24-Hours of Silence", S,
    "Bucket-list goal — go 24 hours without speaking.",
    "Pre-warn people (or carry a note); use writing for essential communication.",
    "Easier on a solo retreat than at home.")

add("Do a Charity Walk", S,
    "Bucket-list goal — participate in a charity walk.",
    "March of Dimes, Susan G. Komen Race, AIDS Walk, Out of the Darkness (suicide prevention).",
    "Fundraising minimums vary; most allow self-funding.")

add("Do a Random Act of Kindness", S,
    "Bucket-list goal — perform a random act of kindness for a stranger.",
    "Pay for the next person's coffee, leave a generous tip, hold a door, compliment specifically.",
    "Trivial entry; meaningful when unobserved.")

add("Donate 100,000 Grains of Rice to Help End World Hunger", S,
    "Bucket-list goal — donate 100,000 grains of rice via Freerice.com.",
    "Each correct trivia question donates 10 grains; 100K grains = 10K questions.",
    "Now run by World Food Programme.")

add("Donate Books", S,
    "Bucket-list goal — donate books to a library or charity.",
    "Local library Friends groups, used bookstores (Better World Books), Little Free Libraries.",
    "Goodwill takes books; many libraries take only specific genres.")

add("Donate Clothing", S,
    "Bucket-list goal — donate clothing.",
    "Goodwill, Salvation Army, Dress for Success (professional attire), homeless shelters (winter gear).",
    "Quality donations only; threadbare clothes get trashed by charities.")

add("Donate Toys at the Holidays", S,
    "Bucket-list goal — donate toys at the holidays.",
    "Toys for Tots (Marines, Christmas), Salvation Army Angel Tree, hospital pediatric wards.",
    "New, unwrapped toys typically required.")

add("Entertain the Elderly at a Nursing Home", S,
    "Bucket-list goal — perform or entertain at a nursing home.",
    "Music, magic, storytelling, holiday programs; activities directors are easy contacts.",
    "Memory care residents respond strongly to era-appropriate music.")

add("Experience a New Religion", S,
    "Bucket-list goal — attend a religious service in a tradition new to you.",
    "Most houses of worship welcome curious visitors; call ahead for guidelines.",
    "Buddhist meditation centers, Quaker meetings, mosque Friday prayers, Jewish Shabbat services.")

add("Feed a Homeless Person", S,
    "Bucket-list goal — feed a homeless person directly.",
    "Buy a meal, hand a sandwich, give a gift card to a nearby restaurant.",
    "Volunteering at a soup kitchen serves more people sustainably.")

add("Find the Meaning of Your Name", S,
    "Bucket-list goal — research the meaning and origin of your name.",
    "BehindTheName.com, Ancestry.com, family genealogy.",
    "Trivial; takes 15 min.")

add("Foster a Puppy", S,
    "Bucket-list goal — foster a puppy or dog.",
    "Local animal shelters and breed-specific rescues need fosters constantly.",
    "Supplies provided by rescue; commit to weeks/months until adoption.")

add("Get a College Degree", S,
    "Bucket-list goal — earn a college degree.",
    "4-year traditional, community college transfer, online universities (WGU, ASU Online).",
    "Adult learner programs accommodate work schedules.")

add("Give a Keynote Speech", S,
    "Bucket-list goal — give a keynote speech.",
    "Industry conferences, association events, university commencement.",
    "Track record of public speaking + recognized expertise required.")

add("Give a TED Talk", S,
    "Bucket-list goal — give a TED talk.",
    "TEDx events accept open speaker applications; main TED is invite-only.",
    "Idea worth spreading + clear delivery + 18-min format.")

add("Give Blood", S,
    "Bucket-list goal — donate blood.",
    "American Red Cross, local blood banks. Whole blood donation every 8 weeks.",
    "30-min process; eat well beforehand.")

add("Give Someone a Hug", S,
    "Bucket-list goal — give someone a meaningful hug.",
    "Trivial entry — but bucket-list version implies unexpected, generous, present-moment hug.",
    "Free Hugs Campaign for organized version.")

add("Give Up Your Seat to Someone", S,
    "Bucket-list goal — give up your seat to someone who needs it more.",
    "Public transit, waiting rooms; offer rather than waiting to be asked.",
    "Trivial bucket entry.")

add("Help an Endangered or Injured Animal", S,
    "Bucket-list goal — help an endangered or injured wild animal.",
    "Call wildlife rehab center; don't handle directly.",
    "Sea turtle nest watch, raptor rehabilitation centers always need volunteers.")

add("Help Someone Who is Lost", S,
    "Bucket-list goal — help a lost stranger.",
    "Direct walk to the destination is more useful than verbal directions.",
    "Trivial; happens often if you're attentive.")

add("Help Someone With a Check on Their Bucket List", S,
    "Bucket-list goal — help someone else complete their bucket list item.",
    "Ask close friends/family what's on their list; offer to help logistically or financially.",
    "Reciprocity often follows.")

add("Learn a New Software Program", S,
    "Bucket-list goal — learn a substantial new software program.",
    "Photoshop, Excel advanced, Blender, Ableton, Final Cut — pick by use case.",
    "Online courses (LinkedIn Learning, Coursera, Udemy) plus active project.")

add("Learn Conversational Spanish", S,
    "Bucket-list goal — speak conversational Spanish.",
    "Duolingo + iTalki tutoring + immersion (Mexico, Guatemala, Spain).",
    "300+ hrs of focused study to reach B1 conversational level.")

add("Learn CPR", S,
    "Bucket-list goal — get CPR certified.",
    "Red Cross or AHA classes (4 hrs, $50–100); lasts 2 years.",
    "Now includes hands-only CPR (no rescue breaths) and AED use.")

add("Learn the Alphabet in Sign Language", S,
    "Bucket-list goal — learn the ASL alphabet.",
    "26 letters; learnable in 1–2 hours of practice.",
    "Lifeprint.com and YouTube tutorials free.")

add("Learn the Heimlich Maneuver", S,
    "Bucket-list goal — learn the Heimlich maneuver.",
    "Included in CPR/First Aid certification courses.",
    "Now called 'abdominal thrusts' in updated guidance; back blows alternated for adults.")

add("Learn to Play a Song on an Instrument", S,
    "Bucket-list goal — learn to play a song on an instrument.",
    "Easy entries: ukulele, harmonica, recorder, drum pad.",
    "One song = ~2 weeks of daily practice; YouTube tutorials abundant.")

add("Learn to Say \"Hello\" in 10 Languages", S,
    "Bucket-list goal — learn to greet in 10 languages.",
    "Hola, Bonjour, Hallo, Ciao, Konnichiwa, Annyeong, Salaam, Namaste, Privet, Olá.",
    "Pronunciation matters more than spelling — Forvo.com for native audio.")

add("List 10 Things I am Grateful For Each Day", S,
    "Bucket-list goal — keep a daily gratitude list.",
    "Daily journaling habit; apps (Day One, Daylio) or paper journal.",
    "Research links gratitude practice to wellbeing markers.")

add("Make a Kiva.com Loan", S,
    "Bucket-list goal — make a microloan on Kiva.org.",
    "$25 minimum loan to entrepreneur; repaid over 6–24 months for relending.",
    "Filter by region, gender, sector to align with personal interest.")

add("Make a Significant Change in Someone's Life", S,
    "Bucket-list goal — make a meaningful difference in someone's life.",
    "Mentoring, financial support, introduction to opportunity, sustained encouragement.",
    "Hard to measure; recognized in retrospect.")

add("Master a New Language", S,
    "Bucket-list goal — reach C1+ fluency in a new language.",
    "1000–2400 hrs of study depending on language difficulty (FSI scale).",
    "Sustained immersion is the only practical path past intermediate.")

add("Meditate", S,
    "Bucket-list goal — establish a meditation practice.",
    "Apps (Waking Up, Headspace, Calm) for guided start; 10–20 min daily for habit.",
    "Vipassana 10-day silent retreats for serious practice (donation-based).")

add("Meet the Dalai Lama", S,
    "Bucket-list goal — meet the Dalai Lama.",
    "Public teachings worldwide; private audience requires connections.",
    "Dharamsala (India) is his residence; Mind & Life conferences feature him.")

add("Participate in a Sweat Lodge Purification Ceremony", S,
    "Bucket-list goal — participate in a sweat lodge.",
    "Authentic ceremonies through Indigenous communities (with respectful invitation only).",
    "Avoid commercial new-age versions; cultural context is the point.")

add("Pay the Bridge Toll for the Person Behind Me", S,
    "Bucket-list goal — pay the toll for the next car.",
    "Increasingly rare with electronic tolling; cash booths still exist on some bridges.",
    "Drive-thru coffee shop equivalent works similarly.")

add("Plant a Tree", S,
    "Bucket-list goal — plant a tree.",
    "Native species in your region; arbor day events plant trees publicly.",
    "Backyard tree, community garden, reforestation volunteering.")

add("Put Change into Someone's Expired Meter", S,
    "Bucket-list goal — feed someone's expired parking meter.",
    "Increasingly rare with app-based meters; cash meters still exist in older cities.",
    "Trivial bucket entry.")

add("Read a Banned Book", S,
    "Bucket-list goal — read a banned book.",
    "ALA's Banned Books Week list (last week of September) is the canonical source.",
    "Recently banned: Maus, Beloved, Brave New World, To Kill a Mockingbird.",
    related=["[[Reading List]]"])

add("Read a Classic Novel", S,
    "Bucket-list goal — read a classic novel.",
    "Modern Library's 100 Best Novels, Norton anthologies, Penguin Classics editions.",
    "Pick by interest, not obligation; abandon if not engaging.",
    related=["[[Reading List]]"])

add("Read a Story to a Child", S,
    "Bucket-list goal — read a bedtime story to a child.",
    "Family children, library story hour volunteering, hospital pediatric reading programs.",
    "Voices and pacing matter more than the choice of book.")

add("Read a Trilogy", S,
    "Bucket-list goal — read all three books in a trilogy.",
    "LOTR, His Dark Materials, Hunger Games, Three Body Problem (Liu Cixin).",
    "Complete in sequence within a season for narrative continuity.",
    related=["[[Reading List]]"])

add("Rescue an Animal", S,
    "Bucket-list goal — adopt a rescue animal.",
    "Local shelters, breed rescues, Petfinder.com for nationwide search.",
    "Adoption fees $50–500; covers spay/neuter and initial vaccinations.")

add("Say \"Thank You\" in 10 Languages", S,
    "Bucket-list goal — say thank you in 10 languages.",
    "Gracias, Merci, Danke, Grazie, Arigato, Kamsahamnida, Shukran, Dhanyavaad, Spasibo, Obrigado.",
    "Pair with greetings for completeness.")

add("Send a Care Package to a Soldier", S,
    "Bucket-list goal — send a care package to a deployed soldier.",
    "Operation Gratitude, Soldiers' Angels, AnySoldier.com.",
    "Standard items: snacks, hygiene products, handwritten letters.")

add("Serve Food at a Soup Kitchen", S,
    "Bucket-list goal — volunteer at a soup kitchen.",
    "Local food banks (Feeding America affiliates), homeless shelters, meal programs.",
    "Holidays oversubscribed — go in February or August when help is sparse.")

add("Send Flowers to Myself", S,
    "Bucket-list goal — send flowers to yourself.",
    "Practice in self-celebration; FTD, 1-800-Flowers, local florist.",
    "Sign card with personal message for full effect.")

add("Spend a Day Helping at a Children's Hospital", S,
    "Bucket-list goal — volunteer for a day at a children's hospital.",
    "Most children's hospitals have volunteer programs (rocking babies, art programs, family room).",
    "Background check + orientation typically required.")

add("Spend the Entire Day By Myself", S,
    "Bucket-list goal — spend a full day alone with no contact.",
    "Phone off or in another room; planned solo activities.",
    "Many find this restorative; others find it confronting.")

add("Spend a Week at a Silent Retreat", S,
    "Bucket-list goal — attend a multi-day silent retreat.",
    "Vipassana 10-day (donation-based) is the rigorous standard; weekend retreats more accessible.",
    "Insight Meditation Society (Barre MA), Spirit Rock (CA).")

add("Sponsor a Child's Wish through Make-a-Wish Foundation", S,
    "Bucket-list goal — sponsor a Make-A-Wish child's wish.",
    "Direct sponsorship via Make-A-Wish foundation; $5K average wish cost.",
    "Volunteer wish granting also available.")

add("Start a Charity", S,
    "Bucket-list goal — start a charity or nonprofit.",
    "501(c)(3) IRS designation, state incorporation, board of directors, ongoing reporting.",
    "Significant ongoing administrative work; consider fiscal sponsorship as alternative.")

add("Teach a Class", S,
    "Bucket-list goal — teach a class.",
    "Adult education, community center workshops, Skillshare/Outschool online.",
    "Pick a topic you can teach with materials and exercises ready.")

add("Unplug for a Week", S,
    "Bucket-list goal — go a week without smartphone or computer.",
    "Pre-warn contacts; use a flip phone for emergency only.",
    "Easier in nature/travel context than at home.")

add("Vote in an Election", S,
    "Bucket-list goal — vote in an election.",
    "Register at vote.gov; check state-specific deadlines and ID requirements.",
    "Local elections often more impactful per vote than national.")

add("Volunteer at a Dog Shelter", S,
    "Bucket-list goal — volunteer at a dog shelter.",
    "Walking, socialization, transport for adoption events, fundraising.",
    "Most shelters require orientation and minimum monthly commitment.")

add("Volunteer at an Orphanage", S,
    "Bucket-list goal — volunteer at an orphanage.",
    "Voluntourism widely criticized for harm to children; vet organizations carefully.",
    "Better alternatives: support local family-based care, fund operations, sustained mentoring.")

add("Write a Book", S,
    "Bucket-list goal — write a book.",
    "NaNoWriMo (November) for fiction first draft (50K words in 30 days).",
    "Self-publish via KDP, Draft2Digital; traditional publishing requires agent + proposal.")

add("Write a Children's Book", S,
    "Bucket-list goal — write a children's book.",
    "Picture book (32 pages, ~500 words) is the standard format.",
    "Illustration usually by separate artist; SCBWI is the standards organization.")

add("Write a Letter to My Future Self", S,
    "Bucket-list goal — write a letter to your future self.",
    "FutureMe.org schedules letters years in advance.",
    "Include current concerns and hopes; deliver 5–10 years out for max impact.")

add("Write a Love Letter", S,
    "Bucket-list goal — write a love letter.",
    "Specific details > generic affection; handwritten on physical paper.",
    "Wax seal and stamp for ceremonial finish.")

add("Write a Poem", S,
    "Bucket-list goal — write a poem.",
    "Form options: free verse (easiest), sonnet, haiku (3 lines), villanelle.",
    "Poetry apps (Poetizer) for community feedback.")

add("Write a Haiku", S,
    "Bucket-list goal — write a haiku.",
    "5-7-5 syllable structure (English); traditional Japanese requires seasonal reference (kigo).",
    "Trivial bucket entry — many people write one in 5 minutes.")


# ============================================================
# WRITER
# ============================================================
def slug(s: str) -> str:
    return s


SECTION_TAG = {
    "adventure": "adventure",
    "exotic-food-drink": "exotic-food-drink",
    "food-drink-experiences": "food-drink-experiences",
    "creative": "creative",
    "style-wellness": "style-wellness",
    "nature-wildlife": "nature-wildlife",
    "finance-luxury": "finance-luxury",
    "entertainment": "entertainment",
    "personal-growth": "personal-growth",
}


def write_item(item: dict, idx: int) -> str:
    folder = VAULT / item["section"]
    folder.mkdir(parents=True, exist_ok=True)
    fp = folder / f"{item['title']}.md"
    if fp.exists():
        return f"SKIP {fp.name} (exists)"

    aliases = item["aliases"]
    aliases_yaml = "[]" if not aliases else "\n" + "\n".join(f"- {a}" for a in aliases)

    tags = ["bucket-list-item", SECTION_TAG[item["section"]]] + item["tags_extra"]
    tags_yaml = "\n" + "\n".join(f"- {t}" for t in tags)

    topics = ["personal/bucket-list", item["section"]] + item["topics_extra"]
    topics_yaml = "\n" + "\n".join(f"- {t}" for t in topics)

    related = ["[[Bucket List]] — parent list"] + item["related"]
    related_lines = "\n".join(f"- {r}" for r in related)

    bullets = "\n".join(f"- {b}" for b in item["bullets"])

    completed_date = ""
    notes_block = ""
    if item["notes"]:
        notes_block = f"\n\n## Notes\n{item['notes']}"

    uid = str(UID_BASE + idx)

    if aliases:
        aliases_field = f"aliases:{aliases_yaml}"
    else:
        aliases_field = "aliases: []"

    content = f"""---
{aliases_field}
bucket_status: {item['status']}
completed_date: {completed_date}
created: {TODAY}
parent: '[[Bucket List]]'
status: published
summary: {item['summary']}
tags:{tags_yaml}
title: {item['title']}
topics:{topics_yaml}
type: reference
uid: '{uid}'
updated: {TODAY}
version: 1
---

# {item['title']}

{item['summary']}

## Why it's on the list
*[your voice — placeholder for personal motivation]*

## How to accomplish
{bullets}{notes_block}

## Related
{related_lines}
"""

    fp.write_text(content)
    return f"WROTE {fp.name}"


def regenerate_moc():
    """Rewrite the parent MOC with all items grouped by section."""
    by_section: dict[str, list[tuple[str, str]]] = {s: [] for s, _ in SECTION_ORDER}
    for item in ITEMS:
        by_section[item["section"]].append((item["title"], item["status"]))
    # also include the items already on disk (Hang Glide, Style & Wellness)
    for sec_slug, _ in SECTION_ORDER:
        sec_dir = VAULT / sec_slug
        if not sec_dir.exists():
            continue
        on_disk = {p.stem for p in sec_dir.glob("*.md")}
        listed = {t for t, _ in by_section[sec_slug]}
        for stem in sorted(on_disk - listed):
            by_section[sec_slug].append((stem, "pending"))

    sections_md = []
    total = 0
    completed = 0
    for sec_slug, sec_label in SECTION_ORDER:
        items = sorted(by_section[sec_slug], key=lambda x: x[0])
        total += len(items)
        completed += sum(1 for _, s in items if s == "completed")
        lines = [f"## {sec_label} ({len(items)})"]
        for title, status in items:
            check = "x" if status == "completed" else " "
            lines.append(f"- [{check}] [[{title}]]")
        sections_md.append("\n".join(lines))

    moc = f"""---
aliases:
- life-goals
- things-to-do
created: 2023-11-22
status: published
summary: Index of personal bucket-list goals across 9 categories. Each item is a separate wiki entry under 07-resources/bucket-list/<section>/.
tags:
- personal
- goals
- bucket-list
- moc
title: Bucket List
topics:
- personal/bucket-list
- personal/goals
type: moc
uid: '20260325004606'
updated: {TODAY}
version: 3
---

# Bucket List

Top-level personal bucket list, organized by category. Each item below is its own wiki entry — click through for "how to accomplish" notes, status, and topical context. Item-level status (the `bucket_status` field on each page) is the source of truth; this index reflects it.

**{total} items across 9 categories. Completed: {completed}.**

{chr(10).join(sections_md)}

## Related
- [[Entertainment Index]]
- [[Food & Nutrition List]]
- [[Reading List]]
- [[Drinks List]]
- [[Camping List]]
- [[Restaurants - RI]]
"""
    (VAULT / "Bucket List.md").write_text(moc)
    return total, completed


if __name__ == "__main__":
    wrote = 0
    skipped = 0
    for i, item in enumerate(ITEMS):
        result = write_item(item, i)
        if result.startswith("WROTE"):
            wrote += 1
        else:
            skipped += 1
    total, completed = regenerate_moc()
    print(f"Wrote {wrote} new files, skipped {skipped} existing.")
    print(f"MOC regenerated: {total} total items, {completed} completed.")
