# Brahmanda

**A Vedic Universe Simulation Engine** — a research tool that spawns a living universe following ancient Hindu cosmological architecture, powered by LLM agents.

> *"Ananta Koti Brahmanda" — Infinite millions of universes*

## What is this?

Brahmanda simulates a single universe cycle (one "breath of Vishnu") where:

- **Brahma** (Creator) generates conscious souls with unique personalities via Claude AI
- **Vishnu** (Maintainer) monitors universe health and deploys Avatars when things go wrong
- **Shiva** (Destroyer) applies entropy, processes death/rebirth, and triggers the final dissolution
- **12-50 Soul Agents** make autonomous decisions each tick — they cooperate, fight, trade, deceive, meditate, and form alliances
- **Maya** (Rendering Engine) filters what each soul can perceive based on their karma, dimension, and cosmic epoch
- **Karma Engine** tracks consequences across multiple lives (samsara/rebirth)

The goal: study **emergent patterns** (do civilizations and belief systems arise?) and **simulation signatures** (do the souls notice they're in a simulation?).

## Architecture

```
┌─────────────────────────────────────────────┐
│              VISHNU (Admin Agent)            │
│   Monitors health, deploys Avatars, patches │
├─────────────────────────────────────────────┤
│     BRAHMA (Creator)  │  SHIVA (Destroyer)  │
│     Spawns entities,  │  Entropy, resets,   │
│     writes rules      │  garbage collection │
├─────────────────────────────────────────────┤
│              YUGA CLOCK (Time Engine)        │
│   4 epochs: Satya → Treta → Dvapara → Kali │
├─────────────────────────────────────────────┤
│              MAYA (Rendering Engine)         │
│   Filters perception by karma/loka/yuga     │
├──────────────┬──────────────┬───────────────┤
│   Svarga     │   Bhu-loka   │    Patala     │
│  (Celestial) │  (Physical)  │ (Subterranean)│
│  Time: 2x   │  Time: 1x    │  Time: 0.5x  │
├──────────────┴──────────────┴───────────────┤
│   KARMA ENGINE  │  DEVAS (Laws) │ ASURAS    │
│   Action→Karma  │  Sun/Water/   │ (Chaos/   │
│   + Samsara     │  Death cycles │  Glitches)│
├─────────────────────────────────────────────┤
│          SOUL AGENTS (LLM-powered)          │
├─────────────────────────────────────────────┤
│          OBSERVER (Research Output)         │
│   Patterns · Signatures · Akashic Records   │
└─────────────────────────────────────────────┘
```

## Quick Start

```bash
# Clone
git clone https://github.com/Saurav12das/Brahmanda.git
cd Brahmanda

# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install anthropic pydantic rich

# Run
ANTHROPIC_API_KEY=sk-your-key python -m brahmanda.main
```

## What Happens During a Run

### Phase 1: Creation (Brahma Exhales)
Brahma generates 12 unique souls with LLM-crafted personalities, desires, and karma seeds. All souls awaken in Bhu-loka (the physical world).

### Phase 2: The Mahayuga Cycle (100 ticks)
The universe progresses through 4 epochs:

| Yuga | Ticks | Character |
|------|-------|-----------|
| **Satya** (Golden) | 40 | High dharma, abundant resources, cooperation |
| **Treta** (Silver) | 30 | Dharma weakens, first conflicts emerge |
| **Dvapara** (Bronze) | 20 | Alliances and wars, balance tips |
| **Kali** (Dark) | 10 | Scarcity, deception, but small virtues amplified |

Each tick:
1. **Devas** enforce natural laws (resource regen, entropy cleansing, disasters)
2. **Asuras** inject chaos (false memories, karma noise, perception fog)
3. **Souls** perceive their world through Maya and decide autonomously
4. **Karma** scores every action; souls can die and be reborn in different dimensions
5. **Vishnu** checks health; deploys Avatars if entropy spikes
6. **Shiva** applies entropy and decay

### Phase 3: Dissolution (Vishnu Inhales)
Shiva dances the Tandava — the universe dissolves. The Observer produces final reports.

## Dimensions (Lokas)

| Loka | Level | Time | Entry Karma | Character |
|------|-------|------|-------------|-----------|
| **Svarga** | 8 | 2x slower | 50 to 100 | Celestial, subtle matter |
| **Bhu** | 7 | 1x (baseline) | -50 to 50 | Physical world |
| **Patala** | 1 | 0.5x slower | -100 to 0 | High-tech, low dharma |

Souls migrate between dimensions based on accumulated karma.

## Research Output

After each run, the Observer produces:

### Emergent Patterns
- Alliance and conflict networks
- Resource inequality (Gini coefficient)
- Faction/group formation
- Cooperation vs. deception rates
- Karma distribution across population

### Simulation Signatures
- **Simulation awareness**: Do souls reference being in a simulation?
- **Emergent cosmology**: Do souls develop belief systems about gods/cycles?
- **Karma quantization**: Discrete value patterns (like Planck-scale effects)
- **Glitch density**: Frequency of Asura-induced anomalies

All data is persisted to `brahmanda.db` (SQLite) for post-run analysis.

## Configuration

Key parameters in `brahmanda/config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `INITIAL_SOUL_COUNT` | 12 | Souls created at genesis |
| `MAX_SOUL_COUNT` | 50 | Population cap |
| `SOUL_MODEL` | claude-sonnet-4-6 | Model for soul decisions |
| `TRINITY_MODEL` | claude-sonnet-4-6 | Model for Brahma/Vishnu |
| `TICKS_PER_YUGA` | 40/30/20/10 | Duration of each epoch |

## Inspired By

The cosmological architecture is drawn from:
- **Vedas** — Multiverse concepts (Ananta Koti Brahmanda)
- **Puranas** — Yuga cycles, 14 Lokas, Vishnu's breathing
- **Mahabharata** — Karma, dharma, avatars
- The **"Are we living in a simulation?"** research question

## Share Your Results!

Run the simulation and share what emerged:
- Did your souls form civilizations?
- Did anyone notice they were in a simulation?
- What patterns appeared in the Kali Yuga?

Open an issue with your Observer report — let's compare universes.

## License

MIT
