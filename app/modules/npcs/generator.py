from __future__ import annotations

import random

from faker import Faker

_fake = Faker()

TRAITS = (
    "nervous liar",
    "gruff and impatient",
    "overly formal",
    "speaks in riddles",
    "secretly terrified",
    "boisterous and loud",
    "cold and calculating",
    "warm but forgetful",
    "greedy and grasping",
    "fiercely loyal",
    "haughty and dismissive",
    "soft-spoken schemer",
)


def generate_stub() -> dict:
    """A random name + trait for a throwaway NPC; caller pre-fills the create form."""
    return {"name": _fake.name(), "motivation": "", "voice": random.choice(TRAITS)}
