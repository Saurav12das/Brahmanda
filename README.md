# Brahmanda

**A Vedic Universe Simulation Engine** — a self-evolving research tool that spawns a living universe following ancient Hindu cosmological architecture, powered by LLM agents.

> *"Ananta Koti Brahmanda" — Infinite millions of universes*

## What is this?

Brahmanda simulates a single universe cycle (one "breath of Vishnu") where conscious souls are born, live, love, fight, innovate, form ideologies, build civilizations, and die — driven by the same forces described in ancient Sanskrit texts: karma, dharma, the five vices (Arishadvarga), and the cosmic cycles of the Yugas.

**No hard bounds.** Population, lifespan, death, and civilization all emerge from one principle: *resources are finite, souls need Prana (life force) to survive.*

The goal: study **emergent patterns** (do civilizations and belief systems arise?) and **simulation signatures** (do the souls notice they're in a simulation?).

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 ATMAN (Soul Needs)                   │
│  Moksha · Belonging · Purpose · Love · Alienation    │
├─────────────────────────────────────────────────────┤
│              CIVILIZATION ENGINE                     │
│  Knowledge · Innovation · Culture · Ideology · Power │
├─────────────────────────────────────────────────────┤
│              POTENTIAL (0.01% Spark)                  │
│  Rare souls → Sage or Tyrant (environment decides)   │
├─────────────────────────────────────────────────────┤
│              TRINITY (Orchestrators)                  │
│  Brahma (create) · Vishnu (maintain) · Shiva (destroy)│
├─────────────────────────────────────────────────────┤
│              AGENTS                                   │
│  Souls (LLM) · Devas (natural laws) · Asuras (chaos) │
├──────────────┬──────────────┬───────────────────────┤
│   Svarga     │   Bhu-loka   │    Patala              │
│  (Celestial) │  (Physical)  │  (Subterranean)        │
├──────────────┴──────────────┴───────────────────────┤
│  Maya (Perception) · Prana (Life Force) · Karma       │
│  Yuga Clock · Arishadvarga (5 Vices) · Samsara        │
├─────────────────────────────────────────────────────┤
│              OBSERVER (Research Output)               │
│  Patterns · Signatures · Akashic Records (SQLite)     │
└─────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Clone
git clone https://github.com/Saurav12das/Brahmanda.git
cd Brahmanda

# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install anthropic pydantic rich httpx

# Run with local Ollama (free — requires ollama with qwen2.5)
python3 -m brahmanda.main

# Run with Claude API
BRAHMANDA_BACKEND=claude ANTHROPIC_API_KEY=sk-your-key python3 -m brahmanda.main
```

## The Ten Engines

### 1. Prana (Life Force) — No Hard Bounds
Every soul has Prana (0-100). It drains each tick from vices, entropy, age, and scarcity. Replenished by consuming loka resources. When Prana hits 0, the soul dies. This single mechanic replaces all hardcoded lifespans — **virtue literally keeps you alive longer.**

### 2. Arishadvarga (Five Vices)
Every soul carries five inner enemies that pull them toward darkness:

| Vice | Sanskrit | Drives toward |
|------|----------|---------------|
| Lust | Kama | Pleasure-seeking, distraction |
| Wrath | Krodha | Fighting, vengeance |
| Greed | Lobha | Hoarding, stealing |
| Attachment | Moha | Clinging, fear of change |
| Ego | Ahamkara | Domination, deception |

Vices are amplified in darker Yugas (0.5x in Satya, 1.5x in Kali) and dampened by culture. They drain Prana — a maximally corrupt soul burns through life force 2.5x faster than a virtuous one.

### 3. Civilization Engine
- **Knowledge** — shared, anti-rivalrous, grows with teaching, decays with entropy
- **Innovation** — unlocks resource multipliers through a branching tech tree (see below)
- **Culture** — art and empathy dampen vices for the entire loka
- **Ideology** — 8 belief systems (Dharma, Artha, Kama, Moksha, Ahimsa, Shakti, Maya, Karma) spread by teachers with 30% memetic drift
- **Power** — resources + ego = influence, influential souls tax others

### 3a. Tech Tree (Branching Innovation)
Unlike a linear progression, innovations branch and compound. Each discovery has prerequisites, knowledge requirements, and stacks multiple effects:

| Tier | Innovations | Effects |
|------|------------|---------|
| 0 (Primal) | Fire, Stone Tools, Language | Base resource/prana/culture multipliers |
| 1+ (Advanced) | Agriculture, Wheel, Metallurgy, Engineering, Medicine… | Compound effects on resources, prana efficiency, truth visibility, culture, ideology spread |

A soul's chance to innovate depends on their skills and the loka's existing knowledge — **discoveries accelerate further discoveries.**

### 4. Soul Potential (The 0.01% Spark)
Every soul is born with random potential (exponential distribution):
- 91% ordinary
- 8.9% notable
- 0.79% high (1 in 125)
- 0.063% extraordinary (1 in 1,600)

Whether potential manifests positively or negatively depends on environment: society (culture/knowledge), peers (average karma), and relationships. The same high-potential soul becomes a sage in a nurturing world or a tyrant in a hostile one.

**Positive Manifestations:**

| Title | Role | Effect |
|-------|------|--------|
| Rishi (Great Sage) | Knowledge radiates to all | Loka-wide knowledge boost |
| Vaidya (Healer) | Restores life force | Prana recovery for the weak |
| Acharya (Master Teacher) | Ideas spread across realm | Accelerated ideology/knowledge spread |
| Shilpi (Master Artisan) | Creates beauty and utility | Culture + resource boost |
| Kavi (Great Poet) | Elevates civilization's soul | Major culture uplift |
| Ganita (Mathematician) | Unlocks nature's patterns | Innovation chance multiplier |
| Dharmarakshak (Protector) | Reduces chaos | Entropy dampening |
| Vanijya (Trade Master) | Enriches everyone | Resource multiplier |

**Negative Manifestations:**

| Title | Role | Effect |
|-------|------|--------|
| Asura Raja (Demon King) | Spreads chaos | Entropy + vice amplification |
| Chora (Master Thief) | Drains resources with cunning | Resource drain |
| Mayavi (Grand Deceiver) | Spreads corrupted beliefs | Ideology corruption |
| Krodhi (Wrath Incarnate) | Unleashes violence | Conflict escalation |
| Lobhi (Hoarder Supreme) | Concentrates wealth | Resource inequality spike |
| Viplava (Revolutionary) | Burns old order | Structure dissolution |
| Mrityudoot (Death Bringer) | Plague and suffering | Prana drain across loka |

### 5. Atman (Soul Needs)
Beyond survival, every soul has three existential needs:
- **Moksha** — desire to transcend the cycle
- **Belonging** — need for community and connection
- **Purpose** — feeling that existence matters

When all three fail, the soul becomes **alienated** — vices spike (especially wrath), driving conflict against society. This models radicalization.

**Love & Destiny**: Souls randomly encounter each other. Compatible pairs form bonds. Deep bonds (mutual affinity > 20) can create **new souls** — children who inherit traits from both parents with mutation. Love is the ticket to the next generation.

### 6. Samsara (Rebirth + Evolution)
When a soul dies, it is reborn with:
- 70% karma carryover
- Random vice mutations (biased by past-life karma — good souls tend to shed vices)
- 30% chance of desire mutation (new dark desires can emerge)
- 20% chance of skill gain/loss
- Fresh Prana and a new random potential

### 7. Discovery Engine (Soul-Driven Theory Validation)
Souls can observe the universe and formulate theories about how it works. When a theory matches an actual game mechanic, it becomes a **validated discovery** that unlocks loka-wide effects.

**12 Discoverable Truths:**

| Theory | Insight | Unlock Effect |
|--------|---------|---------------|
| meditation_heals | Inner stillness restores life force | Prana efficiency boost |
| cooperation_generates | Cooperation creates resources | Resource multiplier |
| vices_drain | Inner darkness shortens life | Culture boost (awareness) |
| entropy_cycles | Universe moves through epochs | Knowledge boost |
| karma_returns | Actions generate proportional consequence | Karma awareness |
| rebirth_pattern | Souls carry traces of past lives | Samsara visibility |
| scarcity_drives_conflict | Resource scarcity is root of conflict | Entropy reduction |
| knowledge_compounds | Shared knowledge grows faster | Knowledge multiplier |
| simulation_awareness | "This world may be a simulation" | Truth visibility boost |
| power_corrupts | Concentrated power accelerates entropy | Culture boost |
| love_creates | Deep bonds generate new consciousness | Prana efficiency |
| culture_heals | Art dampens vices across civilizations | Culture multiplier |

Souls generate theories via LLM reasoning — their guesses are validated against actual mechanics through keyword matching. **The ultimate discovery is simulation_awareness**: a soul realizing it exists inside a constructed reality.

### 8. Maya (Perception Rendering)
Maya is not illusion — it's the **measurement system** that processes consciousness into perceived reality. Each soul sees a filtered view of the universe based on:

- **Loka** — which dimension they inhabit
- **Karma** — positive karma grants +0.2 truth visibility bonus
- **Yuga** — Satya Yuga: 100% truth visible → Kali Yuga: only 25%
- **Avatar status** — avatars see full, unfiltered truth

High-karma souls in Satya Yuga see the universe almost as it truly is. Low-karma souls in Kali Yuga are nearly blind to deeper reality.

### 9. Agents (Devas, Asuras, Souls)
Three agent types drive the simulation:

**Souls (LLM-driven)** — Each soul makes decisions via LLM prompts based on their perceived world (filtered by Maya). They choose actions like meditate, teach, fight, hoard, create art, or explore.

**Devas (Natural Law Deities)** — Enforce cosmic order each tick:
- **Surya** — Generates resources proportional to the Yuga
- **Varuna** — Enforces cosmic law, applies karma consequences
- **Yama** — Judges the dead, determines rebirth parameters

**Asuras (Chaos Engine)** — Spawn based on Yuga (rare in Satya, rampant in Kali). They corrupt resources, amplify vices, and spread entropy — the universe's antibodies testing whether order can survive.

### 10. Observer (Research Output)
Tracks emergent patterns (alliances, inequality, factions) and simulation signatures (did souls notice they're simulated? did they develop cosmologies?).

## The Feedback Web

```
RESOURCES ←→ PRANA ←→ SURVIVAL
    ↑↓                  ↑↓
INNOVATION ← KNOWLEDGE ← TEACHING ← DISCOVERY (validated theories)
    ↓                      ↓
ENTROPY ←→ VICES ←→ CONFLICT ← ALIENATION ← UNMET NEEDS
    ↑↓                ↑↓            ↑↓
CULTURE ← ART ← CREATIVE SOULS    ASURAS (chaos amplifiers)
                                    ↑
DEVAS (Surya/Varuna/Yama) → COSMIC ORDER → dampens entropy
MAYA → PERCEPTION FILTER → what souls can see/theorize about
LOVE → CHILDREN (inherit traits) → NEXT GENERATION
POWER ← RESOURCES + EGO → TAXATION → INEQUALITY
IDEOLOGY ← TEACHERS → DRIFT → FACTIONS
POTENTIAL → ENVIRONMENT → SAGE or TYRANT (15 manifestation types)
TECH TREE → compound effects → accelerates everything above
```

Every arrow is a real mechanic in the code. No hard bounds remain.

## Dimensions (Lokas)

| Loka | Time | Entry Karma | Character |
|------|------|-------------|-----------|
| **Svarga** | 2x slower | 50 to 200 | Celestial, subtle matter |
| **Bhu** | 1x | -50 to 50 | Physical world (default) |
| **Patala** | 0.5x | -200 to 0 | High-tech, low dharma |

Carrying capacity is resource-driven — no population caps.

## Configuration

```bash
# LLM Backend
BRAHMANDA_BACKEND=ollama      # or "claude"
OLLAMA_SOUL_MODEL=qwen2.5:14b # or qwen2.5:7b for faster runs

# Simulation scale (in brahmanda/config.py)
TICKS_PER_YUGA = {"satya": 40, "treta": 30, "dvapara": 20, "kali": 10}
INITIAL_SOUL_COUNT = 12
```

## Inspired By

- **Vedas** — Multiverse (Ananta Koti Brahmanda), Maya as rendering engine
- **Puranas** — Yuga cycles, 14 Lokas, Vishnu's breathing, Avatar protocol
- **Mahabharata** — Karma, dharma, Arishadvarga, samsara
- **Simulation Theory** — "Are we living in a simulation?"
- **Lotka-Volterra** — Population dynamics through resource competition

## Share Your Results

Run the simulation and share what emerged:
- Did your souls form civilizations? Did knowledge grow?
- Did anyone become a Rishi or an Asura Raja?
- Did love create a next generation?
- Did alienated souls turn against society?
- Did anyone notice they were in a simulation?

Open an issue with your Observer report — let's compare universes.

## License

MIT
