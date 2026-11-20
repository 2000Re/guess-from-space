"""題名と説明の翻訳(YouTube の localizations)。視聴者の言語が日本語・スペイン語・フランス語・ドイツ語・ポルトガル語なら、
その言語の題名と説明が表示される。Wait, That Big?(2000Re/wait-that-big の locales.py)と同じ仕組み。AI は使わない。

題名には場所の名前を書かない(答えになるので)ので、題名の型(make_video.TITLES)だけを訳せばよい。
説明は、その言語の1行目のあとに英語の説明(選択肢・答え・出典)をそのまま続ける。
"""
LANGS = ["ja", "es", "fr", "de", "pt"]

# make_video.TITLES の型ごと。{km} は冒頭の写真の幅
TITLES = {
    "classic": {
        "ja": "ここはどこ？🌍 衛星写真クイズ",
        "es": "¿Dónde está este lugar? 🌍 Quiz de satélite",
        "fr": "Où est-ce sur Terre ? 🌍 Quiz satellite",
        "de": "Wo auf der Erde ist das? 🌍 Satelliten-Quiz",
        "pt": "Onde fica este lugar? 🌍 Quiz de satélite",
    },
    "space": {
        "ja": "宇宙から見たこの場所、わかる？🛰️",
        "es": "¿Reconoces este lugar visto desde el espacio? 🛰️",
        "fr": "Reconnais-tu ce lieu vu de l'espace ? 🛰️",
        "de": "Erkennst du diesen Ort aus dem All? 🛰️",
        "pt": "Você reconhece este lugar visto do espaço? 🛰️",
    },
    "photo": {
        "ja": "衛星写真から場所を当てよう 🌍",
        "es": "Adivina el lugar con esta foto de satélite 🌍",
        "fr": "Devine le lieu sur cette photo satellite 🌍",
        "de": "Errate den Ort auf diesem Satellitenfoto 🌍",
        "pt": "Adivinhe o lugar nesta foto de satélite 🌍",
    },
    "width": {
        "ja": "この写真の幅はたった{km}km。ここはどこ？🛰️",
        "es": "Esta foto mide solo {km} km de ancho. ¿Dónde está? 🛰️",
        "fr": "Cette photo ne fait que {km} km de large. Où est-ce ? 🛰️",
        "de": "Dieses Foto ist nur {km} km breit. Wo ist das? 🛰️",
        "pt": "Esta foto tem só {km} km de largura. Onde fica? 🛰️",
    },
    "orbit": {
        "ja": "軌道から見た地球。ここがどこかわかる？🛰️",
        "es": "Visto desde la órbita: ¿sabes dónde es? 🛰️",
        "fr": "Vu depuis l'orbite : sais-tu où c'est ? 🛰️",
        "de": "Aus dem Orbit gesehen: Weißt du, wo das ist? 🛰️",
        "pt": "Visto da órbita: você sabe onde é? 🛰️",
    },
    "zoom": {
        "ja": "ズームアウトして場所を当てよう 🌍",
        "es": "Aleja la vista y adivina el lugar 🌍",
        "fr": "On dézoome : devine le lieu 🌍",
        "de": "Rauszoomen und den Ort erraten 🌍",
        "pt": "Afaste o zoom e adivinhe o lugar 🌍",
    },
    "famous": {
        "ja": "宇宙から見た有名な場所。どこかわかる？🛰️",
        "es": "Un lugar famoso visto desde el espacio. ¿Cuál es? 🛰️",
        "fr": "Un lieu célèbre vu de l'espace. Lequel ? 🛰️",
        "de": "Ein berühmter Ort aus dem All. Welcher ist es? 🛰️",
        "pt": "Um lugar famoso visto do espaço. Qual é? 🛰️",
    },
    "pros": {
        "ja": "地理が得意な人へ：ここはどこ？🌍",
        "es": "Expertos en geografía: ¿dónde está esto? 🌍",
        "fr": "Pros de la géo : où est-ce sur Terre ? 🌍",
        "de": "Geografie-Profis: Wo auf der Erde ist das? 🌍",
        "pt": "Feras de geografia: onde fica isto? 🌍",
    },
    "five_seconds": {
        "ja": "5秒でこの場所がわかる？🛰️",
        "es": "¿Puedes adivinar este lugar en 5 segundos? 🛰️",
        "fr": "Trouveras-tu ce lieu en 5 secondes ? 🛰️",
        "de": "Erkennst du diesen Ort in 5 Sekunden? 🛰️",
        "pt": "Consegue adivinhar este lugar em 5 segundos? 🛰️",
    },
    "above": {
        "ja": "上空から見たこの有名な場所はどこ？🌍",
        "es": "¿Qué lugar famoso es este, visto desde arriba? 🌍",
        "fr": "Quel lieu célèbre est-ce, vu d'en haut ? 🌍",
        "de": "Welcher berühmte Ort ist das, von oben gesehen? 🌍",
        "pt": "Que lugar famoso é este, visto de cima? 🌍",
    },
    "across": {
        "ja": "幅わずか{km}km。この場所を当てられる？🛰️",
        "es": "Solo {km} km de ancho. ¿Adivinas qué lugar es? 🛰️",
        "fr": "À peine {km} km de large. Devines-tu ce lieu ? 🛰️",
        "de": "Nur {km} km breit. Errätst du den Ort? 🛰️",
        "pt": "Só {km} km de largura. Adivinha que lugar é? 🛰️",
    },
    "map_lovers": {
        "ja": "地図好きさんへ：宇宙から見たこの場所、わかる？🌍",
        "es": "Amantes de los mapas: ¿reconocen este lugar desde el espacio? 🌍",
        "fr": "Fans de cartes : reconnaissez-vous ce lieu vu de l'espace ? 🌍",
        "de": "Für Kartenfans: Erkennt ihr diesen Ort aus dem All? 🌍",
        "pt": "Amantes de mapas: reconhecem este lugar visto do espaço? 🌍",
    },
}

# 説明の1行目(その言語)。そのあとに英語の説明をそのまま続ける
LEAD = {
    "ja": "答えが出る前に予想してみてね！🛰️ 衛星写真から有名な場所を当てるクイズです。",
    "es": "¡Adivina antes de la respuesta! 🛰️ Un quiz para reconocer lugares famosos en fotos de satélite.",
    "fr": "Devine avant la réponse ! 🛰️ Un quiz pour reconnaître des lieux célèbres sur des photos satellite.",
    "de": "Rate vor der Auflösung! 🛰️ Ein Quiz: Erkenne berühmte Orte auf Satellitenfotos.",
    "pt": "Adivinhe antes da resposta! 🛰️ Um quiz para reconhecer lugares famosos em fotos de satélite.",
}


def km_text(km, lang):
    """2.8 → "2.8"(英語・日本語)/ "2,8"(ほかの言語)。"""
    s = f"{km:g}"
    return s if lang == "ja" else s.replace(".", ",")


def build(style, number, km, description_en):
    """{言語: {"title", "description"}}。訳のない型なら空(YouTube には英語だけが出る)。"""
    if style not in TITLES:
        return {}
    out = {}
    for lang in LANGS:
        tpl = TITLES[style][lang]
        if "{km}" in tpl:
            if not km:
                continue
            tpl = tpl.format(km=km_text(km, lang))
        title = f"[{number}] {tpl}".replace("<", "‹").replace(">", "›")[:100]
        desc = (LEAD[lang] + "\n\n" + description_en).replace("<", "‹").replace(">", "›")[:4900]
        out[lang] = {"title": title, "description": desc}
    return out
