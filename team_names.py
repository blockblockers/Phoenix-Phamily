"""Canonical team display names, without changing ESPN team IDs or historical names."""
import re
import unicodedata

def team_key(value):
    value = unicodedata.normalize('NFKC', str(value or ''))
    value = value.replace('’', "'").replace('‘', "'").replace('`', "'")
    value = re.sub(r"\s+", " ", value).strip()
    return value.casefold()

def clean_team_name(value):
    value = unicodedata.normalize('NFKC', str(value or ''))
    value = value.replace('’', "'").replace('‘', "'").replace('`', "'")
    return re.sub(r"\s+", " ", value).strip()

def canonical_team_name(raw, aliases=None, personalities=None):
    clean = clean_team_name(raw)
    aliases = aliases or {}
    personalities = personalities or {}
    index = {team_key(k): v for k, v in aliases.items()}
    result = index.get(team_key(clean), clean)
    personality_names = {team_key(k): k for k in personalities}
    return personality_names.get(team_key(result), result)
