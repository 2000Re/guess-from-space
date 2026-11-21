"""Guess From Space の再生リストの決め方(playlists.py が使う)。1本が2つ以上に入ることもある。"""
HISTORIES = ["upload_history.json"]

GAME = ("Real Video Game Places Seen From Space",
        "Real places that are the setting of, or the model for, famous video games, seen in satellite images.")
UNESCO = ("World Heritage Sites Seen From Space",
          "UNESCO World Heritage Sites in satellite images. Can you name them?")
NATURE = ("Volcanoes, Lakes and Wonders of Nature From Space",
          "Famous volcanoes, lakes, canyons and other natural wonders in satellite images.")
CITIES = ("Cities, Coasts and Islands From Space",
          "Famous cities, coastlines and islands in satellite images. Can you name them?")


def for_record(rec):
    import places as P
    key = rec.get("key", "")
    p = next((x for x in P.ALL_PLACES if P.key(x) == key), None)
    if p is None:
        return []
    if p.get("game"):
        return [GAME]
    out = [NATURE if key in P.NATURE else CITIES]
    if p.get("unesco"):
        out.append(UNESCO)
    return out
