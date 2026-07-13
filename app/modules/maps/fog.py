from __future__ import annotations


def reduce_ops(ops: list[dict]) -> list[dict]:
    """Normalize an ordered fog op list.

    Base map state is fully fogged. 'reveal' punches holes; 'hide' re-fogs.
    A reveal-all ({type:'all'}) makes all priors irrelevant -> just that reveal.
    A hide-all ({type:'all'}) returns to fully fogged -> empty list.
    """
    result: list[dict] = []
    for entry in ops:
        geom = entry.get("geom", {})
        if geom.get("type") == "all":
            if entry["op"] == "reveal":
                result = [{"op": "reveal", "geom": {"type": "all"}}]
            else:  # hide-all
                result = []
            continue
        result.append({"op": entry["op"], "geom": geom})
    return result
