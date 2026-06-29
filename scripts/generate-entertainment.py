#!/usr/bin/env python3
"""Generate per-item book/movie/TV pages and the three sub-MOCs.

One-shot generator. Writes files under 07-resources/entertainment/{reading,movies,tv}/.
Skips files that already exist.
"""
from __future__ import annotations
from pathlib import Path

VAULT = Path("/home/turbobeest/vault/07-resources/entertainment")
TODAY = "2026-05-03"
UID_BASE = 20260503150000

ITEMS: list[dict] = []


def add(
    title: str,
    section: str,           # 'reading' | 'movies' | 'tv'
    summary: str,
    *bullets: str,
    aliases: list[str] | None = None,
    related: list[str] | None = None,
    status: str = "queued",  # queued | in-progress | finished | dropped
    finished_date: str = "",
    extra_fm: dict | None = None,
    why: str | None = None,  # user voice — fills 'Why it's on the list' verbatim
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
            "finished_date": finished_date,
            "extra_fm": extra_fm or {},
            "why": why,
        }
    )


SECTION_META = {
    "reading": {
        "label": "Reading List",
        "moc_title": "Reading List",
        "tag": "reading-list-item",
        "extra_tag": "books",
        "topic": "entertainment/reading",
        "type_label": "book",
    },
    "movies": {
        "label": "Watchlist - Movies",
        "moc_title": "Watchlist - Movies",
        "tag": "watchlist-item",
        "extra_tag": "movies",
        "topic": "entertainment/film",
        "type_label": "movie",
    },
    "tv": {
        "label": "Watchlist - TV Shows",
        "moc_title": "Watchlist - TV Shows",
        "tag": "watchlist-item",
        "extra_tag": "tv",
        "topic": "entertainment/television",
        "type_label": "TV series",
    },
}


# ============================================================
# READING LIST (11 books)
# ============================================================

add("Good Reasons for Bad Feelings", "reading",
    "Evolutionary psychiatry — why anxiety, depression, and other distressing feelings persist despite causing suffering.",
    "Author: Randolph M. Nesse, MD (founder of evolutionary medicine).",
    "Year: 2019. Genre: psychology / evolutionary biology.",
    "Argument: distressing emotions are adaptive responses, not malfunctions — but mismatched to modern life.",
    aliases=["good-reasons", "nesse"],
    extra_fm={"author": "Randolph M. Nesse", "year": 2019, "genre": "psychology"})

add("Unfuckology", "reading",
    "Self-help built on behavioral psychology and evolutionary biology — building courage and self-respect through action.",
    "Author: Amy Alkon (advice columnist 'The Advice Goddess').",
    "Year: 2018. Genre: self-help / behavioral psychology.",
    "Original title 'Unf*ckology' (asterisked); core thesis: act first, feel second.",
    aliases=["unf-ckology", "alkon"],
    extra_fm={"author": "Amy Alkon", "year": 2018, "genre": "self-help"})

add("The Coddling of the American Mind", "reading",
    "How three 'great untruths' are shaping younger generations and undermining mental health and free inquiry on US campuses.",
    "Authors: Jonathan Haidt and Greg Lukianoff.",
    "Year: 2018. Genre: social psychology / cultural criticism.",
    "Untruths: fragility, emotional reasoning, us-vs-them. Pre-pandemic argument that aged into a cultural touchstone.",
    aliases=["coddling", "haidt-lukianoff"],
    extra_fm={"author": "Jonathan Haidt & Greg Lukianoff", "year": 2018, "genre": "social-psychology"})

add("Algorithm Design Manual", "reading",
    "Practical reference and textbook on algorithm design strategies — the standard alternative to CLRS for self-study.",
    "Author: Steven Skiena.",
    "Year: 2008 (2nd ed); 2020 (3rd ed). Genre: computer science / algorithms.",
    "Two-part structure: techniques (sorting, graphs, dynamic programming) + catalog of common problems with solutions.",
    aliases=["skiena", "algorithm-design"],
    extra_fm={"author": "Steven Skiena", "year": 2008, "genre": "computer-science"})

add("Three Body Problem", "reading",
    "Hard sci-fi opener of the 'Remembrance of Earth's Past' trilogy — first-contact story rooted in physics, history, and game theory.",
    "Author: Liu Cixin (translator: Ken Liu).",
    "Year: 2008 (Chinese), 2014 (English). Hugo Award 2015.",
    "Continues with The Dark Forest and Death's End — both arguably stronger than book one.",
    aliases=["3-body", "liu-cixin", "santi"],
    why="Best hard sci-fi ever.",
    extra_fm={"author": "Liu Cixin", "year": 2008, "genre": "sci-fi"})

add("Gothic Violence", "reading",
    "Modern revenge thriller — pulp action with literary ambition, written for kinetic readability.",
    "Author: Adam Lane Smith.",
    "Year: 2022. Genre: action / thriller.",
    "Self-published; cult following in indie-fiction circles.",
    aliases=["gothic-violence-smith"],
    why="Live leak but in a book.",
    extra_fm={"author": "Adam Lane Smith", "year": 2022, "genre": "thriller"})

add("Wherever You Go There You Are", "reading",
    "Foundational text on mindfulness meditation — short, accessible introduction to MBSR.",
    "Author: Jon Kabat-Zinn (founder of Mindfulness-Based Stress Reduction).",
    "Year: 1994. Genre: mindfulness / psychology.",
    "Short essays, not a how-to manual — orientation rather than instruction.",
    aliases=["kabat-zinn", "wherever-you-go"],
    why="Psychology for hormones.",
    extra_fm={"author": "Jon Kabat-Zinn", "year": 1994, "genre": "mindfulness"})

add("Musashi", "reading",
    "Epic novelization of Miyamoto Musashi's life — 17th-century Japanese swordsman, philosopher, author of The Book of Five Rings.",
    "Author: Eiji Yoshikawa (translator: Charles S. Terry).",
    "Year: 1939 (serialized), English 1981. Genre: historical fiction / philosophy.",
    "1,150+ pages; foundational text in samurai-fiction canon. Pair with Musashi's own Book of Five Rings.",
    aliases=["yoshikawa", "miyamoto-musashi"],
    why="Samurai, man shit, philosophy.",
    extra_fm={"author": "Eiji Yoshikawa", "year": 1939, "genre": "historical-fiction"})

add("Permutation City", "reading",
    "Hard sci-fi exploring simulation theory, identity, and consciousness — what is it to exist as code?",
    "Author: Greg Egan.",
    "Year: 1994. Genre: hard sci-fi / philosophy of mind.",
    "Foundational text in simulation/uploaded-consciousness fiction; precedes The Matrix conceptually.",
    aliases=["egan", "permutation"],
    why="Simulation theory, future.",
    extra_fm={"author": "Greg Egan", "year": 1994, "genre": "sci-fi"})

add("Zero to One", "reading",
    "Founder-mindset book on building genuinely new businesses — from the PayPal Mafia perspective.",
    "Author: Peter Thiel (with Blake Masters).",
    "Year: 2014. Genre: startups / business strategy.",
    "Key thesis: monopoly is a feature, not a bug — competition erodes profit.",
    aliases=["zero-to-one-thiel"],
    extra_fm={"author": "Peter Thiel", "year": 2014, "genre": "business"})

add("DataHead", "reading",
    "Career book for entering data science — pathways, skills, projects, interview prep.",
    "Author: TBD — multiple books titled similarly; user to confirm exact source.",
    "Year: TBD. Genre: data-science career.",
    "Flag for user verification: title needs author/year confirmation.",
    aliases=["data-head"],
    extra_fm={"author": "TBD", "year": "TBD", "genre": "data-science"})


# ============================================================
# WATCHLIST - MOVIES (42: 41 from chronological table + Slammin' Salmon moved from TV)
# ============================================================

add("2001 - A Space Odyssey", "movies",
    "Stanley Kubrick's monumental sci-fi meditation on evolution, intelligence, and humanity's place in the cosmos.",
    "Year: 1968. Director: Stanley Kubrick. Themes: AI, evolution, transcendence.",
    "HAL 9000 is the foundational AI antagonist; Strauss's Also Sprach Zarathustra forever associated with this film.",
    aliases=["2001"],
    extra_fm={"year": 1968, "director": "Stanley Kubrick", "genre": "sci-fi"})

add("Silent Running", "movies",
    "Ecological sci-fi about the last botanist tending Earth's surviving plants in space, alongside three drone helpers.",
    "Year: 1972. Director: Douglas Trumbull. Themes: ecology, isolation, AI companions.",
    "Bruce Dern's Freeman Lowell is one of cinema's first sympathetic eco-protagonists.",
    extra_fm={"year": 1972, "director": "Douglas Trumbull", "genre": "sci-fi"})

add("Logan's Run", "movies",
    "Dystopian future where citizens are euthanized at age 30 — a 'runner' uncovers what lies beyond.",
    "Year: 1976. Director: Michael Anderson. Themes: dystopia, age, control.",
    "Visually iconic 70s sci-fi; concept aged better than execution.",
    extra_fm={"year": 1976, "director": "Michael Anderson", "genre": "sci-fi"})

add("The Man Who Fell to Earth", "movies",
    "An alien arrives on Earth seeking water for his dying planet; capitalism, addiction, and isolation consume him.",
    "Year: 1976. Director: Nicolas Roeg. Star: David Bowie.",
    "Bowie's first major film role; cult classic of alienation cinema.",
    extra_fm={"year": 1976, "director": "Nicolas Roeg", "genre": "sci-fi"})

add("Blade Runner", "movies",
    "Neo-noir cyberpunk about a 'blade runner' hunting bioengineered replicants in 2019 LA — what does it mean to be human?",
    "Year: 1982. Director: Ridley Scott. Source: Philip K. Dick's 'Do Androids Dream of Electric Sheep?'.",
    "Multiple cuts exist; Final Cut (2007) is the definitive version. Foundational cyberpunk visual language.",
    extra_fm={"year": 1982, "director": "Ridley Scott", "genre": "cyberpunk"})

add("Tron", "movies",
    "Programmer is digitized into a computer system and must fight for survival against a tyrannical AI.",
    "Year: 1982. Director: Steven Lisberger. Star: Jeff Bridges.",
    "Pioneering CGI; visual aesthetic influenced 40 years of digital design.",
    extra_fm={"year": 1982, "director": "Steven Lisberger", "genre": "sci-fi"})

add("War Games", "movies",
    "A teenage hacker accidentally accesses a military supercomputer programmed to play global thermonuclear war for real.",
    "Year: 1983. Director: John Badham. Star: Matthew Broderick.",
    "Defined hacker-in-cinema archetype; 'shall we play a game?' is canon.",
    aliases=["wargames"],
    extra_fm={"year": 1983, "director": "John Badham", "genre": "thriller"})

add("The Terminator", "movies",
    "Cyborg assassin sent from 2029 to kill the future mother of humanity's resistance leader.",
    "Year: 1984. Director: James Cameron. Star: Arnold Schwarzenegger.",
    "Launched a franchise; original is leaner and more menacing than any sequel.",
    extra_fm={"year": 1984, "director": "James Cameron", "genre": "sci-fi"})

add("Brazil", "movies",
    "Bureaucratic dystopia where a low-level functionary's daydreams collide with state machinery — Orwell meets Monty Python.",
    "Year: 1985. Director: Terry Gilliam. Star: Jonathan Pryce.",
    "Studio cut vs Gilliam's cut famous battle; Criterion edition collects both.",
    extra_fm={"year": 1985, "director": "Terry Gilliam", "genre": "dystopia"})

add("RoboCop", "movies",
    "Slain Detroit cop is resurrected as a corporate-owned cyborg; satire of Reaganite capitalism and privatized policing.",
    "Year: 1987. Director: Paul Verhoeven. Star: Peter Weller.",
    "Sharper political satire than its action exterior suggests.",
    extra_fm={"year": 1987, "director": "Paul Verhoeven", "genre": "sci-fi"})

add("The Running Man", "movies",
    "In a televised dystopian gameshow, condemned prisoners are hunted on live TV.",
    "Year: 1987. Director: Paul Michael Glaser. Star: Arnold Schwarzenegger.",
    "Loosely from Stephen King novel (as Richard Bachman); predicted reality TV's logical extreme.",
    extra_fm={"year": 1987, "director": "Paul Michael Glaser", "genre": "sci-fi"})

add("Akira", "movies",
    "Post-apocalyptic Neo-Tokyo, biker gangs, and government psychic experiments — landmark animated sci-fi.",
    "Year: 1988. Director: Katsuhiro Otomo. Genre: animated cyberpunk.",
    "Single-handedly opened Western audiences to anime as serious cinema.",
    extra_fm={"year": 1988, "director": "Katsuhiro Otomo", "genre": "anime-cyberpunk"})

add("Total Recall", "movies",
    "Construction worker buys implanted memories of a Mars vacation — and discovers he may be a covert agent.",
    "Year: 1990. Director: Paul Verhoeven. Star: Arnold Schwarzenegger.",
    "From Philip K. Dick's 'We Can Remember It For You Wholesale'; reality vs memory ambiguity preserved.",
    extra_fm={"year": 1990, "director": "Paul Verhoeven", "genre": "sci-fi"})

add("Ghost in the Shell", "movies",
    "Cyborg detective hunts a hacker who can override human consciousness — foundational anime cyberpunk.",
    "Year: 1995. Director: Mamoru Oshii. Genre: animated cyberpunk.",
    "Direct visual and thematic influence on The Matrix.",
    extra_fm={"year": 1995, "director": "Mamoru Oshii", "genre": "anime-cyberpunk"})

add("Hackers", "movies",
    "Teenage hackers stumble onto a corporate conspiracy in mid-90s NYC.",
    "Year: 1995. Director: Iain Softley. Stars: Jonny Lee Miller, Angelina Jolie.",
    "Cult classic; aesthetics outweigh accuracy. Inspired the 'Movies for Hackers' list this watchlist references.",
    extra_fm={"year": 1995, "director": "Iain Softley", "genre": "thriller"})

add("Johnny Mnemonic", "movies",
    "Data courier ferries information in his brain through a cyberpunk future.",
    "Year: 1995. Director: Robert Longo. Star: Keanu Reeves.",
    "From William Gibson short story; feature is uneven but the source material is foundational cyberpunk.",
    extra_fm={"year": 1995, "director": "Robert Longo", "genre": "cyberpunk"})

add("12 Monkeys", "movies",
    "Convict from a future devastated by plague is sent back in time to find the source of the outbreak.",
    "Year: 1995. Director: Terry Gilliam. Stars: Bruce Willis, Brad Pitt.",
    "Inspired by Chris Marker's La Jetée; non-linear time loop.",
    extra_fm={"year": 1995, "director": "Terry Gilliam", "genre": "sci-fi"})

add("Gattaca", "movies",
    "Genetically inferior man assumes another's identity to pursue space travel in a eugenics-stratified future.",
    "Year: 1997. Director: Andrew Niccol. Stars: Ethan Hawke, Uma Thurman, Jude Law.",
    "Restrained sci-fi; the science fiction is mostly social, not technological.",
    extra_fm={"year": 1997, "director": "Andrew Niccol", "genre": "sci-fi"})

add("Wag The Dog", "movies",
    "Spin doctor and a Hollywood producer fabricate a war to distract from a presidential scandal.",
    "Year: 1997. Director: Barry Levinson. Stars: Robert De Niro, Dustin Hoffman.",
    "Released weeks before the Lewinsky scandal broke — eerie prescience.",
    extra_fm={"year": 1997, "director": "Barry Levinson", "genre": "satire"})

add("Dark City", "movies",
    "Man wakes amnesiac in a city where memories aren't his and night never ends.",
    "Year: 1998. Director: Alex Proyas. Star: Rufus Sewell.",
    "Released months before The Matrix with strikingly similar themes; deserves more credit.",
    extra_fm={"year": 1998, "director": "Alex Proyas", "genre": "sci-fi"})

add("The Matrix", "movies",
    "Hacker discovers reality is a simulation maintained by machines harvesting humanity's body heat.",
    "Year: 1999. Directors: The Wachowskis. Star: Keanu Reeves.",
    "Cultural milestone; bullet-time, leather coats, and 'red pill' all enter the global vocabulary.",
    extra_fm={"year": 1999, "director": "The Wachowskis", "genre": "cyberpunk"})

add("A.I. Artificial Intelligence", "movies",
    "Childlike android programmed to love is abandoned by his adoptive family — a Pinocchio story for the digital age.",
    "Year: 2001. Director: Steven Spielberg (from Stanley Kubrick's project).",
    "Spielberg directed Kubrick's developed concept after Kubrick's death; tonal split is famous.",
    aliases=["ai-spielberg"],
    extra_fm={"year": 2001, "director": "Steven Spielberg", "genre": "sci-fi"})

add("Minority Report", "movies",
    "Future cop-leader of a precrime unit becomes a suspect when precogs predict he'll murder a stranger.",
    "Year: 2002. Director: Steven Spielberg. Star: Tom Cruise.",
    "From Philip K. Dick story; gestural UI design influenced a decade of interface design.",
    extra_fm={"year": 2002, "director": "Steven Spielberg", "genre": "sci-fi"})

add("Primer", "movies",
    "Two engineers accidentally build a time machine in their garage — and the consequences spiral.",
    "Year: 2004. Director: Shane Carruth. Budget: $7,000.",
    "Densest time-travel logic in any film; requires multiple viewings + a flowchart.",
    extra_fm={"year": 2004, "director": "Shane Carruth", "genre": "sci-fi"})

add("Eternal Sunshine of the Spotless Mind", "movies",
    "Heartbroken couple hire a service to erase memories of each other from their minds.",
    "Year: 2004. Director: Michel Gondry. Writer: Charlie Kaufman.",
    "Memory erasure as metaphor for grief; one of Carrey's most restrained performances.",
    aliases=["eternal-sunshine"],
    extra_fm={"year": 2004, "director": "Michel Gondry", "genre": "sci-fi"})

add("Idiocracy", "movies",
    "Average soldier wakes 500 years in the future to find civilization devastatingly stupider.",
    "Year: 2006. Director: Mike Judge. Star: Luke Wilson.",
    "Released to little fanfare; aged into prophetic territory.",
    extra_fm={"year": 2006, "director": "Mike Judge", "genre": "satire"})

add("Iron Man", "movies",
    "Weapons mogul Tony Stark builds a high-tech suit to escape captivity, then becomes a superhero.",
    "Year: 2008. Director: Jon Favreau. Star: Robert Downey Jr.",
    "Launched the MCU; Downey's improvised performance defined modern blockbuster acting.",
    extra_fm={"year": 2008, "director": "Jon Favreau", "genre": "superhero"})

add("Moon", "movies",
    "Lone astronaut on a 3-year lunar mining mission discovers things are not what they seem.",
    "Year: 2009. Director: Duncan Jones. Star: Sam Rockwell.",
    "Independent sci-fi; Rockwell carries the entire film.",
    extra_fm={"year": 2009, "director": "Duncan Jones", "genre": "sci-fi"})

add("Avatar", "movies",
    "Paraplegic marine inhabits an alien body to infiltrate a tribe on a moon being strip-mined by humans.",
    "Year: 2009. Director: James Cameron.",
    "Highest-grossing film for over a decade; defined modern 3D filmmaking.",
    extra_fm={"year": 2009, "director": "James Cameron", "genre": "sci-fi"})

add("The Social Network", "movies",
    "Founding of Facebook, told through the lawsuits — Aaron Sorkin script, David Fincher direction.",
    "Year: 2010. Director: David Fincher. Star: Jesse Eisenberg.",
    "Soundtrack by Trent Reznor / Atticus Ross; defining film about the platform era.",
    extra_fm={"year": 2010, "director": "David Fincher", "genre": "drama"})

add("Prometheus", "movies",
    "Alien-prequel exploring the origins of humanity and the Engineers who created — and want to destroy — us.",
    "Year: 2012. Director: Ridley Scott.",
    "Ambitious in concept, divisive in execution; aged better than its release-time reception.",
    extra_fm={"year": 2012, "director": "Ridley Scott", "genre": "sci-fi"})

add("Her", "movies",
    "Lonely letter-writer in near-future LA falls in love with his AI operating system.",
    "Year: 2013. Director: Spike Jonze. Stars: Joaquin Phoenix, Scarlett Johansson (voice).",
    "Designed visual aesthetic became a 2020s reference for warm-toned future fiction.",
    extra_fm={"year": 2013, "director": "Spike Jonze", "genre": "sci-fi"})

add("The Zero Theorem", "movies",
    "Reclusive computer programmer searches for the meaning of life via a corporate-assigned 'Zero Theorem' project.",
    "Year: 2013. Director: Terry Gilliam. Star: Christoph Waltz.",
    "Late-period Gilliam; the spiritual closer of his Brazil/12 Monkeys dystopia trilogy.",
    extra_fm={"year": 2013, "director": "Terry Gilliam", "genre": "dystopia"})

add("The Imitation Game", "movies",
    "Alan Turing leads the WWII Bletchley Park team that broke the Nazi Enigma cipher.",
    "Year: 2014. Director: Morten Tyldum. Star: Benedict Cumberbatch.",
    "Liberties taken with history; revived public attention on Turing's persecution and posthumous pardon.",
    extra_fm={"year": 2014, "director": "Morten Tyldum", "genre": "biopic"})

add("Ex Machina", "movies",
    "Programmer is invited to test a billionaire's prototype humanoid AI — but the test is not what it seems.",
    "Year: 2014. Director: Alex Garland. Stars: Domhnall Gleeson, Alicia Vikander, Oscar Isaac.",
    "Tight three-hander; one of the sharpest AI-consciousness films of the 2010s.",
    extra_fm={"year": 2014, "director": "Alex Garland", "genre": "sci-fi"})

add("Interstellar", "movies",
    "Astronaut farmers travel through a wormhole to find humanity a new home.",
    "Year: 2014. Director: Christopher Nolan.",
    "Kip Thorne's physics consultation; the black hole visualization led to a published paper.",
    extra_fm={"year": 2014, "director": "Christopher Nolan", "genre": "sci-fi"})

add("Tomorrowland", "movies",
    "Disillusioned scientist and bright teenage girl discover a hidden city of optimistic futurism.",
    "Year: 2015. Director: Brad Bird. Star: George Clooney.",
    "Critically mixed; thematic counterprogramming to dystopia-saturated 2010s sci-fi.",
    extra_fm={"year": 2015, "director": "Brad Bird", "genre": "sci-fi"})

add("Arrival", "movies",
    "Linguist is recruited to communicate with aliens who have arrived in twelve enormous shells around the world.",
    "Year: 2016. Director: Denis Villeneuve. Star: Amy Adams.",
    "From Ted Chiang's 'Story of Your Life'; the rare first-contact film centered on language and grief.",
    extra_fm={"year": 2016, "director": "Denis Villeneuve", "genre": "sci-fi"})

add("Dune", "movies",
    "Noble heir to a desert-planet fiefdom navigates prophecy, ecology, and political assassination.",
    "Year: 2021. Director: Denis Villeneuve.",
    "Part 1 of two; succeeded where Lynch's 1984 and the SciFi miniseries struggled.",
    aliases=["dune-villeneuve"],
    extra_fm={"year": 2021, "director": "Denis Villeneuve", "genre": "sci-fi"})

add("Oppenheimer", "movies",
    "J. Robert Oppenheimer leads the Manhattan Project, then watches the consequences unfold.",
    "Year: 2023. Director: Christopher Nolan. Star: Cillian Murphy.",
    "Won Best Picture 2024; biggest-budget biographical drama in modern memory.",
    extra_fm={"year": 2023, "director": "Christopher Nolan", "genre": "biopic"})

add("The Recruit", "movies",
    "Spy thriller — note: original list entry is ambiguous (could be the 2003 film with Colin Farrell, or the 2022 Netflix series).",
    "Year: TBD. Flag for user verification — title needs disambiguation.",
    "Likely the 2003 Roger Donaldson film with Al Pacino and Colin Farrell.",
    extra_fm={"year": "TBD", "director": "TBD", "genre": "thriller"})

# Slammin' Salmon — moved here from TV (it's a 2009 Broken Lizard film, not a series)
add("Slammin' Salmon", "movies",
    "Comedy about an ex-boxer running a Miami restaurant who motivates his staff with a high-stakes sales contest.",
    "Year: 2009. Director: Kevin Heffernan. Production: Broken Lizard troupe.",
    "Routed here from the original TV watchlist; it's a film, not a series.",
    aliases=["slammin-salmon"],
    extra_fm={"year": 2009, "director": "Kevin Heffernan", "genre": "comedy"})


# ============================================================
# WATCHLIST - TV (19: 6 from existing TV list + 13 from movies "Unsorted" section)
# ============================================================

add("For All Mankind", "tv",
    "Alternate-history sci-fi: the USSR beats the US to the Moon, kicking off a never-ending space race.",
    "Network: Apple TV+. Years: 2019–present. Genre: alternate-history sci-fi.",
    "Created by Ronald D. Moore (Battlestar Galactica). Each season jumps a decade.",
    extra_fm={"network": "Apple TV+", "year": 2019, "genre": "sci-fi"})

add("Ascension", "tv",
    "Generation-ship miniseries — what happens when the truth about the journey is not what the crew was told.",
    "Network: Syfy / Amazon. Year: 2014. Genre: sci-fi miniseries.",
    "Six episodes; a contained, single-twist story. Self-contained, no cliffhanger continuation.",
    extra_fm={"network": "Syfy", "year": 2014, "genre": "sci-fi"})

add("Silent Sea", "tv",
    "Korean lunar-base sci-fi thriller — research team retrieves a sample from an abandoned moon facility.",
    "Network: Netflix. Year: 2021. Genre: Korean sci-fi thriller.",
    "Eight episodes; Bae Doona stars. Tonally restrained.",
    aliases=["the-silent-sea"],
    extra_fm={"network": "Netflix", "year": 2021, "genre": "sci-fi"})

add("Station Eleven", "tv",
    "Post-pandemic limited series following a traveling Shakespeare company 20 years after a flu wipes out civilization.",
    "Network: HBO Max. Year: 2021. Genre: post-apocalyptic literary drama.",
    "From Emily St. John Mandel novel; one of the best-reviewed limited series of its year.",
    extra_fm={"network": "HBO Max", "year": 2021, "genre": "drama"})

add("WandaVision", "tv",
    "MCU series unfolding through pastiches of sitcoms across the decades — and grief processed through fantasy.",
    "Network: Disney+. Year: 2021. Genre: superhero / experimental.",
    "First MCU streaming series; widely regarded as the most formally inventive Marvel project.",
    extra_fm={"network": "Disney+", "year": 2021, "genre": "superhero"})

add("Tacoma FD", "tv",
    "Workplace comedy about an under-utilized fire department in Tacoma, WA — Broken Lizard's TV vehicle.",
    "Network: truTV / Max. Years: 2019–2023. Genre: comedy.",
    "From the Broken Lizard troupe (Super Troopers, Beerfest); 4 seasons.",
    extra_fm={"network": "truTV", "year": 2019, "genre": "comedy"})

# 13 entries moved from Movies "Also Recommended (Unsorted)" — all are TV series
add("Longmire", "tv",
    "Modern-Western crime drama set in fictional Absaroka County, Wyoming.",
    "Network: A&E (S1–3) / Netflix (S4–6). Years: 2012–2017. Genre: neo-Western crime.",
    "From Craig Johnson's Walt Longmire mystery novels.",
    extra_fm={"network": "A&E / Netflix", "year": 2012, "genre": "crime"})

add("Blue Eye Samurai", "tv",
    "Animated revenge epic in Edo-period Japan — a mixed-race outcast hunts the four white men who could be her father.",
    "Network: Netflix. Year: 2023. Genre: animated historical action.",
    "Created by Amber Noizumi and Michael Green; renewed for season 2.",
    extra_fm={"network": "Netflix", "year": 2023, "genre": "anime-action"})

add("Ripley", "tv",
    "Black-and-white Patricia Highsmith adaptation — Andrew Scott as the elegant con man Tom Ripley.",
    "Network: Netflix. Year: 2024. Genre: limited series / psychological thriller.",
    "Steven Zaillian's adaptation; visually distinct from the 1999 Damon film.",
    extra_fm={"network": "Netflix", "year": 2024, "genre": "thriller"})

add("Travelers", "tv",
    "Future operatives' consciousnesses are sent back into present-day hosts to prevent the collapse of civilization.",
    "Network: Showcase / Netflix. Years: 2016–2018. Genre: sci-fi.",
    "Three seasons; Eric McCormack stars. Cancelled before its larger arc resolved.",
    extra_fm={"network": "Netflix", "year": 2016, "genre": "sci-fi"})

add("Bloodline", "tv",
    "Florida Keys family-secrets drama — the return of the black-sheep brother destabilizes everything.",
    "Network: Netflix. Years: 2015–2017. Genre: drama / thriller.",
    "From the Damages creators; tense, slow-burn family pathology.",
    extra_fm={"network": "Netflix", "year": 2015, "genre": "drama"})

add("The Last Kingdom", "tv",
    "Saxon-raised Dane navigates the unification of England under Alfred the Great.",
    "Network: BBC / Netflix. Years: 2015–2022. Genre: historical drama.",
    "From Bernard Cornwell's Saxon Stories novels; followed by Seven Kings Must Die film.",
    extra_fm={"network": "BBC / Netflix", "year": 2015, "genre": "historical-drama"})

add("The Fall of the House of Usher", "tv",
    "Mike Flanagan's Edgar Allan Poe-soaked horror miniseries — a pharma dynasty collapses across eight episodes.",
    "Network: Netflix. Year: 2023. Genre: horror miniseries.",
    "Each episode adapts a different Poe story or character; the Flanagan stock company in full force.",
    extra_fm={"network": "Netflix", "year": 2023, "genre": "horror"})

add("The OA", "tv",
    "Blind woman returns home with her sight restored, claiming knowledge of dimensions beyond death.",
    "Network: Netflix. Years: 2016–2019. Genre: metaphysical sci-fi.",
    "Cancelled after 2 seasons; intended as 5-part arc. Cult following continues.",
    extra_fm={"network": "Netflix", "year": 2016, "genre": "sci-fi"})

add("Waco - American Apocalypse", "tv",
    "Three-part Netflix documentary on the 1993 Branch Davidian siege.",
    "Network: Netflix. Year: 2023. Genre: documentary miniseries.",
    "Includes never-before-seen footage and FBI/ATF interview material.",
    aliases=["waco-american-apocalypse"],
    extra_fm={"network": "Netflix", "year": 2023, "genre": "documentary"})

add("Supernatural", "tv",
    "Two brothers hunt demons, ghosts, and gods across America for 15 seasons.",
    "Network: WB / The CW. Years: 2005–2020. Genre: urban fantasy / horror.",
    "327 episodes; one of the longest-running American sci-fi/fantasy series.",
    extra_fm={"network": "The CW", "year": 2005, "genre": "fantasy"})

add("3%", "tv",
    "Brazilian dystopian sci-fi — every 20-year-old competes for one of the 3% of spots in an offshore utopia.",
    "Network: Netflix. Years: 2016–2020. Genre: dystopian sci-fi.",
    "First Brazilian Netflix Original; four seasons, complete arc.",
    aliases=["3-percent", "tres-por-cento"],
    extra_fm={"network": "Netflix", "year": 2016, "genre": "sci-fi"})

add("Arcane", "tv",
    "Animated origin story for League of Legends characters Vi and Jinx — set across the cities of Piltover and Zaun.",
    "Network: Netflix. Years: 2021–2024. Genre: animated steampunk drama.",
    "Studio Fortiche animation; widely considered some of the best animated TV ever produced.",
    extra_fm={"network": "Netflix", "year": 2021, "genre": "animation"})

add("Outer Banks", "tv",
    "North Carolina teen treasure-hunters — divisions between locals (Pogues) and rich kids (Kooks) drive the drama.",
    "Network: Netflix. Years: 2020–present. Genre: teen adventure.",
    "Multi-season ongoing; mass-appeal Netflix YA hit.",
    extra_fm={"network": "Netflix", "year": 2020, "genre": "teen-adventure"})


# ============================================================
# WRITER
# ============================================================

def write_item(item: dict, idx: int) -> str:
    section = item["section"]
    meta = SECTION_META[section]
    folder = VAULT / section
    folder.mkdir(parents=True, exist_ok=True)
    fp = folder / f"{item['title']}.md"
    if fp.exists():
        return f"SKIP {fp.name}"

    aliases = item["aliases"]
    aliases_field = "aliases: []" if not aliases else "aliases:\n" + "\n".join(f"- {a}" for a in aliases)

    tags = [meta["tag"], meta["extra_tag"]]
    tags_yaml = "\n".join(f"- {t}" for t in tags)

    topics = [meta["topic"]]
    topics_yaml = "\n".join(f"- {t}" for t in topics)

    related = [f"[[{meta['moc_title']}]] — parent list"] + item["related"]
    related_lines = "\n".join(f"- {r}" for r in related)

    bullets = "\n".join(f"- {b}" for b in item["bullets"])

    extra_fm_lines = ""
    for k, v in item["extra_fm"].items():
        extra_fm_lines += f"\n{k}: {v}"

    why_section = (
        f"## Why it's on the list\n{item['why']}\n"
        if item["why"]
        else "## Why it's on the list\n*[your voice — placeholder for personal motivation]*\n"
    )

    uid = str(UID_BASE + idx)

    content = f"""---
{aliases_field}
consumption_status: {item['status']}
finished_date: {item['finished_date']}
created: {TODAY}
parent: '[[{meta['moc_title']}]]'
status: published
summary: {item['summary']}
tags:
{tags_yaml}
title: {item['title']}
topics:
{topics_yaml}
type: reference
uid: '{uid}'
updated: {TODAY}
version: 1{extra_fm_lines}
---

# {item['title']}

{item['summary']}

{why_section}
## Notes
{bullets}

## Related
{related_lines}
"""
    fp.write_text(content)
    return f"WROTE {fp.name}"


def write_moc(section: str) -> tuple[int, int]:
    meta = SECTION_META[section]
    folder = VAULT / section
    items_on_disk = sorted(p.stem for p in folder.glob("*.md") if p.stem != meta["moc_title"])

    # Read consumption_status from each
    import re
    pat = re.compile(r"^consumption_status:\s*(\S+)\s*$", re.MULTILINE)
    rows: list[tuple[str, str]] = []
    finished = 0
    for stem in items_on_disk:
        text = (folder / f"{stem}.md").read_text()
        m = pat.search(text)
        st = (m.group(1).strip() if m else "queued")
        rows.append((stem, st))
        if st == "finished":
            finished += 1

    lines = [f"## {section.title() if section != 'tv' else 'TV Shows'} ({len(rows)})"]
    for stem, st in rows:
        check = "x" if st == "finished" else " "
        lines.append(f"- [{check}] [[{stem}]]")
    body = "\n".join(lines)

    moc = f"""---
aliases:
- {section}-list
created: 2023-11-22
status: published
summary: {meta['label']} — index of per-{meta['type_label']} pages under 07-resources/entertainment/{section}/.
tags:
- entertainment
- {meta['extra_tag']}
- moc
title: {meta['moc_title']}
topics:
- {meta['topic']}
type: moc
uid: '20260503160000'
updated: {TODAY}
version: 1
---

# {meta['moc_title']}

Per-{meta['type_label']} entries live in `07-resources/entertainment/{section}/`. Per-item `consumption_status` is the source of truth (values: `queued | in-progress | finished | dropped`); this index reflects it.

**{len(rows)} {meta['type_label']}s. Finished: {finished}.**

{body}

## Related
- [[Reading List]]
- [[Watchlist - Movies]]
- [[Watchlist - TV Shows]]
- [[Bucket List]]
"""
    (folder / f"{meta['moc_title']}.md").write_text(moc)
    return len(rows), finished


if __name__ == "__main__":
    wrote = 0
    skipped = 0
    for i, item in enumerate(ITEMS):
        result = write_item(item, i)
        if result.startswith("WROTE"):
            wrote += 1
        else:
            skipped += 1
    print(f"Items: wrote {wrote}, skipped {skipped}.")

    for sec in ("reading", "movies", "tv"):
        n, fin = write_moc(sec)
        print(f"  {SECTION_META[sec]['moc_title']}: {n} entries, {fin} finished.")
