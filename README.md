# Brahmanda

**A Vedic Universe Simulation Engine** -- a self-evolving research tool that spawns a living universe following ancient Hindu cosmological architecture, powered by LLM agents.

> *"Ananta Koti Brahmanda" -- Infinite millions of universes*

## What is this?

Brahmanda simulates a single universe cycle (one "breath of Vishnu") where conscious souls are born, live, love, fight, innovate, form ideologies, build civilizations, and die -- driven by the same forces described in ancient Sanskrit texts: karma, dharma, the five vices (Arishadvarga), and the cosmic cycles of the Yugas.

**No hard bounds.** Population, lifespan, death, and civilization all emerge from one principle: *resources are finite, souls need Prana (life force) to survive.*

**Every run is a unique universe.** A built-in randomizer shuffles the laws of physics (prana rates, karma scores, yuga parameters, tech tree, and 70+ other constants) at startup using a reproducible seed.

The goal: study **emergent patterns** (do civilizations and belief systems arise?) and **simulation signatures** (do the souls notice they're in a simulation?).

## Architecture

```
+---------------------------------------------------------+
|                 ATMAN (Soul Needs)                       |
|  Moksha . Belonging . Purpose . Love . Alienation        |
+---------------------------------------------------------+
|              HOPE <-> DESPAIR SPECTRUM                   |
|  Contagious . Fatigue . Breaking Point . Group Correction|
+---------------------------------------------------------+
|              CIVILIZATION ENGINE                         |
|  Knowledge . Innovation . Culture . Ideology . Power     |
|  Akashic Memory (cultural inheritance across generations)|
+---------------------------------------------------------+
|              POTENTIAL (0.01% Spark)                      |
|  Rare souls -> Sage or Tyrant (environment decides)      |
+---------------------------------------------------------+
|              TRINITY (Orchestrators)                      |
|  Brahma (create) . Vishnu (maintain) . Shiva (destroy)   |
+---------------------------------------------------------+
|              AGENTS                                      |
|  Souls (LLM) . Devas (natural laws) . Asuras (chaos)    |
+----------------+----------------+-----------------------+
|   Svarga       |   Bhu-loka     |    Patala             |
|  (Celestial)   |  (Physical)    |  (Subterranean)       |
+----------------+----------------+-----------------------+
|  Maya (Perception) . Prana (Life Force) . Karma          |
|  Yuga Clock . Arishadvarga (5 Vices) . Samsara           |
+---------------------------------------------------------+
|  RANDOMIZER (unique laws of physics per universe)        |
+---------------------------------------------------------+
|              OBSERVER (Research Output)                   |
|  Patterns . Signatures . Akashic Records (SQLite)        |
+---------------------------------------------------------+
```

---

## Quick Start

### Prerequisites

- Python 3.9+
- An LLM backend (see options below)

### Install

```bash
git clone https://github.com/Saurav12das/Brahmanda.git
cd Brahmanda
pip install -r requirements.txt
```

### Run

```bash
# Default: uses Ollama with gemma4:31b
python3 -m brahmanda.main

# With a specific seed (reproducible universe):
BRAHMANDA_SEED=42 python3 -m brahmanda.main

# Custom soul count:
BRAHMANDA_SOULS=10 python3 -m brahmanda.main
```

---

## LLM Backend Setup

Brahmanda works with **any LLM that speaks the OpenAI-compatible API** or the Anthropic API. Here's how to set up each provider:

### Option 1: Ollama (Local, Free) -- Recommended for experimentation

[Install Ollama](https://ollama.com), then pull a model:

```bash
# Recommended models (pick one):
ollama pull gemma4          # ~10GB, good balance of speed and quality
ollama pull gemma4:31b      # ~19GB, best quality, slower
ollama pull qwen2.5:14b     # ~9GB, fast, good JSON output
ollama pull llama3.1:8b     # ~5GB, fastest, decent quality

# Run the simulation:
OLLAMA_SOUL_MODEL=gemma4 OLLAMA_TRINITY_MODEL=gemma4 python3 -m brahmanda.main
```

**Tips for Ollama:**
- Smaller models (7-8B) are faster but produce simpler soul decisions
- Larger models (14-31B) produce richer emergent behavior but are slower
- If you see timeouts, try a smaller model or reduce `BRAHMANDA_SOULS`

### Option 2: Anthropic Claude API

```bash
export BRAHMANDA_BACKEND=claude
export ANTHROPIC_API_KEY=sk-ant-your-key-here

python3 -m brahmanda.main
```

Uses `claude-haiku-4-5-20251001` by default (fast and cheap). To change models, edit `CLAUDE_SOUL_MODEL` and `CLAUDE_TRINITY_MODEL` in `brahmanda/config.py`.

### Option 3: OpenAI-compatible APIs (GPT, Grok, Groq, Together, etc.)

Brahmanda's Ollama backend works with **any OpenAI-compatible endpoint**. Just point the Ollama URL to your provider:

**OpenAI:**
```bash
# You'll need an OpenAI-compatible proxy or use LiteLLM:
pip install litellm
litellm --model gpt-4o-mini --port 11434

OLLAMA_URL=http://localhost:11434 python3 -m brahmanda.main
```

**Grok (xAI):**
```bash
# Use LiteLLM as a proxy:
pip install litellm
export XAI_API_KEY=your-grok-key
litellm --model xai/grok-2 --port 11434

OLLAMA_URL=http://localhost:11434 python3 -m brahmanda.main
```

**Groq (ultra-fast inference):**
```bash
pip install litellm
export GROQ_API_KEY=your-groq-key
litellm --model groq/llama-3.3-70b-versatile --port 11434

OLLAMA_URL=http://localhost:11434 python3 -m brahmanda.main
```

**Together AI / Fireworks / any OpenAI-compatible provider:**
```bash
pip install litellm
export TOGETHER_API_KEY=your-key  # or FIREWORKS_API_KEY, etc.
litellm --model together_ai/meta-llama/Llama-3.3-70B-Instruct --port 11434

OLLAMA_URL=http://localhost:11434 python3 -m brahmanda.main
```

**LM Studio (local GUI):**
```bash
# 1. Download LM Studio from https://lmstudio.ai
# 2. Load any model and start the local server (default port 1234)
OLLAMA_URL=http://localhost:1234 python3 -m brahmanda.main
```

### Model Recommendations

| Provider | Model | Speed | Quality | Cost |
|----------|-------|-------|---------|------|
| Ollama | `gemma4` | Fast | Good | Free |
| Ollama | `gemma4:31b` | Slow | Excellent | Free |
| Ollama | `qwen2.5:14b` | Fast | Good | Free |
| Anthropic | `claude-haiku-4-5` | Very fast | Excellent | ~$0.01/run |
| Groq | `llama-3.3-70b` | Ultra fast | Excellent | Free tier |
| xAI | `grok-2` | Fast | Excellent | Pay per use |
| Together | `Llama-3.3-70B` | Fast | Excellent | Pay per use |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BRAHMANDA_BACKEND` | `ollama` | LLM backend: `ollama` or `claude` |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama (or compatible) API URL |
| `OLLAMA_SOUL_MODEL` | `gemma4:31b` | Model for soul decisions |
| `OLLAMA_TRINITY_MODEL` | `gemma4:31b` | Model for Brahma/Vishnu/Shiva |
| `ANTHROPIC_API_KEY` | (none) | Required if using Claude backend |
| `BRAHMANDA_SEED` | (random) | Reproducible universe seed |
| `BRAHMANDA_SOULS` | `5` | Initial number of souls |
| `BRAHMANDA_DB` | `brahmanda.db` | SQLite database path |

---

## The Twelve Engines

### 1. Prana (Life Force) -- No Hard Bounds
Every soul has Prana (0-100). It drains each tick from vices, entropy, age, and scarcity. Replenished by consuming loka resources. When Prana hits 0, the soul dies. **Virtue literally keeps you alive longer.**

### 2. Arishadvarga (Five Vices)
Every soul carries five inner enemies that pull them toward darkness:

| Vice | Sanskrit | Drives toward |
|------|----------|---------------|
| Lust | Kama | Pleasure-seeking, distraction |
| Wrath | Krodha | Fighting, vengeance |
| Greed | Lobha | Hoarding, stealing |
| Attachment | Moha | Clinging, fear of change |
| Ego | Ahamkara | Domination, deception |

Vices are amplified in darker Yugas and dampened by culture and hope.

### 3. Hope / Despair Spectrum
Every soul carries a hope value from -1.0 (deep despair) to +1.0 (high hope):

- **Hope** slows prana drain, dampens vices, amplifies virtuous actions
- **Hope fatigue** -- above 0.5, benefits diminish. Above 0.7, complacency sets in (souls stop striving)
- **Despair breaking point** -- below -0.5, vices spike exponentially. Below -0.7, souls become capable of extreme evil
- **Contagion** -- hope/despair spreads between bonded souls with diminishing returns, hard-capped at +/-0.8
- **Group correction** -- if an entire loka drifts past +/-0.6, a gentle regression prevents runaway spirals

### 4. Civilization Engine
- **Knowledge** -- shared, anti-rivalrous, grows with teaching, decays with entropy
- **Innovation** -- branching tech tree with compounding effects
- **Culture** -- art and empathy dampen vices for the entire loka
- **Ideology** -- 8 belief systems spread by teachers with memetic drift
- **Power** -- resources + ego = influence, influential souls tax others
- **Akashic Memory** -- loka-level cultural memory that accumulates discoveries, inventions, and elder teachings. Inherited by every newborn and reborn soul, enabling knowledge to compound across generations

### 5. Soul Potential (The 0.01% Spark)
Every soul is born with random potential. Whether it manifests positively or negatively depends entirely on environment: society, peers, and relationships. The same soul becomes a sage in a nurturing world or a tyrant in a hostile one.

**15 manifestation types** -- from Rishi (Great Sage) to Mrityudoot (Death Bringer).

### 6. Atman (Soul Needs)
Three existential needs beyond survival: **Moksha** (transcendence), **Belonging** (community), **Purpose** (meaning). When all three fail, the soul becomes alienated -- vices spike, driving conflict.

**Love & Destiny**: Compatible soul pairs form bonds. Deep bonds create new souls -- children who inherit traits, vices, hope, and family memories from both parents.

### 7. Samsara (Rebirth + Evolution)
When a soul dies, it is reborn with karma carryover, vice mutations, a past-life memory echo, and cultural knowledge inherited from the Akashic Memory of their birth loka.

### 8. Discovery Engine
Souls observe patterns and formulate theories. When a theory matches an actual game mechanic, it becomes a validated discovery. **12 discoverable truths**, including the ultimate: *simulation_awareness* -- a soul realizing it exists inside a constructed reality.

### 9. Emergent Science
Souls can found entirely new fields of science by combining existing innovations and discoveries. Each run produces a unique scientific tradition -- two universes will never develop the same tree.

### 10. Maya (Perception Rendering)
Each soul sees a filtered view of the universe based on their loka, karma, yuga, and hope level. High-karma souls in Satya Yuga see reality clearly. Low-karma souls in Kali Yuga are nearly blind.

### 11. Agents (Devas, Asuras, Souls)
- **Souls (LLM-driven)** -- make decisions based on perceived world, vices, hope, and inherited memories
- **Devas** -- enforce natural laws (resource generation, entropy cleansing, natural disasters)
- **Asuras** -- chaos agents that corrupt resources, inject false memories, scramble relationships

### 12. Randomized Universe Laws
Every simulation run randomizes 70+ constants with a reproducible seed: prana rates, karma scores, yuga parameters, tech tree probabilities, hope thresholds, and more. No two universes have the same physics. Print the seed to reproduce any interesting run.

---

## Knowledge Inheritance (How Civilizations Compound)

Three layers ensure knowledge persists and compounds across generations:

| Layer | Mechanism | When |
|-------|-----------|------|
| **Akashic Memory** | Loka-level cultural bank: discoveries, inventions, legends, elder teachings (max 15 entries) | Inherited at birth/rebirth |
| **Parent -> Child** | Children inherit condensed memories from both parents | Love-generation birth |
| **Past Life Echo** | Dying soul's most impactful action is condensed into one memory for their next life | Samsara rebirth |

This means a discovery at tick 5 can influence a soul born at tick 50 through cultural memory -- exactly how real civilizations work.

---

## The Feedback Web

```
RESOURCES <-> PRANA <-> SURVIVAL
    |                    |
INNOVATION <- KNOWLEDGE <- TEACHING <- DISCOVERY
    |                      |
ENTROPY <-> VICES <-> CONFLICT <- ALIENATION <- UNMET NEEDS
    |                  |               |
CULTURE <- ART     ASURAS         DESPAIR -> EVIL (exponential)
                                  HOPE -> dampens vices (with fatigue)
AKASHIC MEMORY -> inherited by newborns -> COMPOUNDS knowledge
LOVE -> CHILDREN (inherit traits + memories) -> NEXT GENERATION
POWER <- RESOURCES + EGO -> TAXATION -> INEQUALITY
RANDOMIZER -> unique physics per universe -> every run is different
```

---

## Dimensions (Lokas)

| Loka | Time | Entry Karma | Character |
|------|------|-------------|-----------|
| **Svarga** | 2x slower | 50 to 200 | Celestial, subtle matter |
| **Bhu** | 1x | -50 to 50 | Physical world (default) |
| **Patala** | 0.5x | -200 to 0 | High-tech, low dharma |

---

## Inspired By

- **Vedas** -- Multiverse (Ananta Koti Brahmanda), Maya as rendering engine
- **Puranas** -- Yuga cycles, 14 Lokas, Vishnu's breathing, Avatar protocol
- **Mahabharata** -- Karma, dharma, Arishadvarga, samsara
- **Simulation Theory** -- "Are we living in a simulation?"
- **Lotka-Volterra** -- Population dynamics through resource competition

## Share Your Results

Run the simulation and share what emerged:
- Did your souls form civilizations? Did knowledge grow?
- Did anyone become a Rishi or an Asura Raja?
- Did love create a next generation?
- Did alienated souls turn against society?
- Did anyone notice they were in a simulation?
- What sciences did your universe invent?
- How did hope and despair shape the civilization?

Open an issue with your Observer report -- let's compare universes.

## License

MIT
