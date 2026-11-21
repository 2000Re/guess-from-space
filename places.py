"""クイズに出す場所のリスト。

衛星写真(Sentinel-2 cloudless 2016、約10m/画素)で、数km以上の大きな形として見分けられる、
世界遺産・有名観光地を選んでいる。建物単位の名所(エッフェル塔、タージ・マハル、ピラミッドなど)は小さくて
ぼやけるので入れない。画像は2016年のものなので、それ以降にできたものも入れない。

各項目:
  name     正解(画面と読み上げ)。"The" で始まる名前は、読み上げでは "the" にする
  country  国(画面に出す)
  where    読み上げの「It's <name>, <where>!」の部分。省略すると "in <country>"
  lon, lat 中心(答えの印を出す場所)
  start    冒頭の寄りの窓の幅(km)。形の一部だけが見えて、何だろう?と思わせる広さ
  end      いちばん引いたときの窓の幅(km)。省略すると END_KM
  wrong    外れの選択肢2つ(同じ地域や似た地形の、実在の場所)
  note     ひとこと(画面と読み上げ)。事実だけを書く。世界遺産と書くのは、実際に登録されているものだけ
  unesco   世界遺産(またはその一部)なら True(説明欄のハッシュタグに使う)

場所を足したら python tools/check_places.py で、中心が合っているか、形が見えるかを確かめる。
"""

END_KM = 60

UNESCO = "A UNESCO World Heritage Site"

PLACES = [
    # ---------------------------------------------------------------- ヨーロッパ
    dict(name="Venice", country="Italy", lon=12.3360, lat=45.4375, start=2.8, wrong=["Amsterdam", "St. Petersburg"],
         note=UNESCO, unesco=True),
    dict(name="Mont-Saint-Michel", country="France", lon=-1.5115, lat=48.6361, start=2.5,
         wrong=["St Michael's Mount", "Lindisfarne"], note="A tidal island and UNESCO World Heritage Site",
         unesco=True),
    dict(name="Santorini", country="Greece", lon=25.3960, lat=36.4040, start=9, end=40, wrong=["Milos", "Mykonos"],
         note="An island ring around a flooded volcanic caldera"),
    dict(name="Mount Vesuvius", country="Italy", lon=14.4260, lat=40.8210, start=3.5, wrong=["Mount Etna", "Stromboli"],
         note="The volcano that buried Pompeii in 79 AD"),
    dict(name="Mount Etna", country="Italy", lon=14.9934, lat=37.7510, start=6, wrong=["Mount Vesuvius", "Mount Teide"],
         note=UNESCO, unesco=True),
    dict(name="Stromboli", country="Italy", lon=15.2130, lat=38.7890, start=3.5, end=40, wrong=["Vulcano", "Santorini"],
         note="One of the Aeolian Islands, a UNESCO World Heritage Site", unesco=True),
    dict(name="Palmanova", country="Italy", lon=13.3100, lat=45.9054, start=2.5, end=30,
         wrong=["Naarden", "Bourtange"], note="A star-shaped fortress town and UNESCO World Heritage Site", unesco=True),
    dict(name="Lake Como", country="Italy", lon=9.2570, lat=45.9870, start=6, wrong=["Lake Garda", "Lake Geneva"],
         note="A Y-shaped lake at the foot of the Alps"),
    dict(name="Paris", country="France", lon=2.3470, lat=48.8540, start=4, wrong=["London", "Berlin"],
         note="The banks of the Seine are a UNESCO World Heritage Site", unesco=True),
    dict(name="London", country="United Kingdom", lon=-0.0754, lat=51.5055, start=4, wrong=["Paris", "Prague"],
         note="Home to the Tower of London, a UNESCO World Heritage Site", unesco=True),
    dict(name="Amsterdam", country="Netherlands", lon=4.8897, lat=52.3700, start=3, wrong=["Copenhagen", "Bruges"],
         where="in the Netherlands", note="Its 17th-century canal ring is a UNESCO World Heritage Site", unesco=True),
    dict(name="Saint Petersburg", country="Russia", lon=30.3141, lat=59.9386, start=4, wrong=["Stockholm", "Helsinki"],
         note="Its historic centre is a UNESCO World Heritage Site", unesco=True),
    dict(name="Barcelona", country="Spain", lon=2.1650, lat=41.3930, start=3.5, wrong=["Valencia", "Marseille"],
         note="Famous for the street grid of the Eixample"),
    dict(name="Gibraltar", country="British Overseas Territory", lon=-5.3536, lat=36.1408, start=3.5,
         wrong=["Ceuta", "Monaco"], where="on the southern coast of the Iberian Peninsula",
         note="A British Overseas Territory with a runway across its isthmus"),
    dict(name="Bay of Kotor", country="Montenegro", lon=18.6900, lat=42.4500, start=8, wrong=["Geirangerfjord", "Lake Como"],
         note=UNESCO, unesco=True),
    dict(name="Geirangerfjord", country="Norway", lon=7.1600, lat=62.1050, start=6,
         wrong=["Milford Sound", "Bay of Kotor"], note="Part of the West Norwegian Fjords, a UNESCO World Heritage Site",
         unesco=True),
    dict(name="Mount Teide", country="Spain", lon=-16.6421, lat=28.2724, start=6, wrong=["Mount Etna", "Mount Pico"],
         where="on Tenerife, Spain", note="Teide National Park is a UNESCO World Heritage Site", unesco=True),
    dict(name="Istanbul", country="Turkey", lon=28.9784, lat=41.0082, start=5, wrong=["Lisbon", "Naples"],
         note="Its historic areas are a UNESCO World Heritage Site", unesco=True),
    dict(name="Mount Ararat", country="Turkey", lon=44.2983, lat=39.7016, start=8,
         wrong=["Mount Damavand", "Mount Elbrus"], note="The highest mountain in Turkey"),

    # ---------------------------------------------------------------- アフリカ・中東
    dict(name="Mount Kilimanjaro", country="Tanzania", lon=37.3556, lat=-3.0674, start=8,
         wrong=["Mount Kenya", "Mount Meru"], note="The highest mountain in Africa", unesco=True),
    dict(name="Ngorongoro Crater", country="Tanzania", lon=35.5880, lat=-3.1800, start=18,
         wrong=["Masai Mara", "Amboseli"], note=UNESCO, unesco=True),
    dict(name="Victoria Falls", country="Zambia / Zimbabwe", lon=25.8572, lat=-17.9243, start=3,
         wrong=["Iguazu Falls", "Niagara Falls"], where="on the border of Zambia and Zimbabwe", note=UNESCO,
         unesco=True),
    dict(name="Table Mountain", country="South Africa", lon=18.4038, lat=-33.9628, start=5,
         wrong=["Sugarloaf Mountain", "Mount Roraima"], where="in Cape Town, South Africa",
         note="Part of the Cape Floral Region, a UNESCO World Heritage Site", unesco=True),
    dict(name="Sossusvlei", country="Namibia", lon=15.2900, lat=-24.7300, start=7, wrong=["Erg Chebbi", "Wadi Rum"],
         note="Famous for its red sand dunes"),
    dict(name="The Eye of the Sahara", country="Mauritania", lon=-11.4010, lat=21.1240, start=12, end=90,
         wrong=["Tassili n'Ajjer", "Wadi Rum"], note="A giant ring-shaped rock formation"),
    dict(name="Mount Nyiragongo", country="DR Congo", lon=29.2475, lat=-1.5200, start=4,
         wrong=["Mount Kilimanjaro", "Erta Ale"], where="in the Democratic Republic of the Congo",
         note="Inside Virunga National Park, a UNESCO World Heritage Site", unesco=True),
    dict(name="Le Morne Brabant", country="Mauritius", lon=57.3200, lat=-20.4600, start=6, wrong=["Mahé", "Bora Bora"],
         note=UNESCO, unesco=True),
    dict(name="Palm Jumeirah", country="United Arab Emirates", lon=55.1385, lat=25.1150, start=3.5,
         wrong=["The Pearl-Qatar", "Durrat Al Bahrain"], where="in Dubai", note="An artificial island shaped like a palm tree"),
    dict(name="The World Islands", country="United Arab Emirates", lon=55.1700, lat=25.2240, start=5,
         wrong=["Palm Jebel Ali", "The Pearl-Qatar"], where="in Dubai",
         note="Artificial islands laid out like a map of the world"),
    dict(name="Mount Damavand", country="Iran", lon=52.1090, lat=35.9550, start=8, wrong=["Mount Ararat", "Mount Elbrus"],
         note="The highest peak in Iran"),

    # ---------------------------------------------------------------- アジア
    dict(name="Mount Fuji", country="Japan", lon=138.7274, lat=35.3606, start=7,
         wrong=["Mount Kilimanjaro", "Mount Rainier"], note=UNESCO, unesco=True),
    dict(name="Sakurajima", country="Japan", lon=130.6570, lat=31.5850, start=7, wrong=["Mount Vesuvius", "Stromboli"],
         note="One of Japan's most active volcanoes"),
    dict(name="The Forbidden City", country="China", lon=116.3972, lat=39.9169, start=2.0, end=30,
         wrong=["Gyeongbokgung Palace", "Hue Imperial City"], where="in Beijing, China", note=UNESCO, unesco=True),
    dict(name="Three Gorges Dam", country="China", lon=111.0030, lat=30.8230, start=4, wrong=["Hoover Dam", "Itaipu Dam"],
         note="The world's largest power station by capacity"),
    dict(name="Shanghai", country="China", lon=121.4990, lat=31.2390, start=5, wrong=["Hong Kong", "Guangzhou"],
         note="The Huangpu River curves past the Pudong skyline"),
    dict(name="Hong Kong", country="China", lon=114.1694, lat=22.2930, start=5, wrong=["Singapore", "Shanghai"],
         note="Victoria Harbour lies between Hong Kong Island and Kowloon"),
    dict(name="Mount Bromo", country="Indonesia", lon=112.9530, lat=-7.9425, start=5,
         wrong=["Mount Rinjani", "Mount Batur"], note="An active volcano inside the Tengger caldera"),
    dict(name="Krakatoa", country="Indonesia", lon=105.4230, lat=-6.1020, start=4, end=40,
         wrong=["Stromboli", "Taal Volcano"], note="Famous for its huge eruption in 1883"),
    dict(name="Mayon Volcano", country="Philippines", lon=123.6850, lat=13.2570, start=7,
         wrong=["Mount Fuji", "Mount Taranaki"], where="in the Philippines", note="Famous for its near-perfect cone"),
    dict(name="Malé", country="Maldives", lon=73.5093, lat=4.1755, start=2.5, end=30, wrong=["Funafuti", "Majuro"],
         where="in the Maldives", note="The capital of the Maldives"),
    dict(name="Rock Islands", country="Palau", lon=134.3800, lat=7.2200, start=6, wrong=["Phang Nga Bay", "El Nido"],
         note=UNESCO, unesco=True),

    # ---------------------------------------------------------------- オセアニア
    dict(name="Uluru", country="Australia", lon=131.0369, lat=-25.3444, start=4.5, wrong=["Wave Rock", "Mount Augustus"],
         note=UNESCO, unesco=True),
    dict(name="Sydney", country="Australia", lon=151.2153, lat=-33.8568, start=4.5, wrong=["Auckland", "San Francisco"],
         note="Home to the Sydney Opera House, a UNESCO World Heritage Site", unesco=True),
    dict(name="Whitehaven Beach", country="Australia", lon=149.0260, lat=-20.2420, start=4,
         wrong=["Byron Bay", "Jervis Bay"], note="Famous for the swirling sands of Hill Inlet"),
    dict(name="Wineglass Bay", country="Australia", lon=148.2960, lat=-42.1670, start=5,
         wrong=["Whitehaven Beach", "Jervis Bay"], where="in Tasmania, Australia",
         note="A curved bay in Freycinet National Park"),
    dict(name="Wolfe Creek Crater", country="Australia", lon=127.7937, lat=-19.1717, start=2.5, end=30,
         wrong=["Meteor Crater", "Tenoumer Crater"], note="A meteorite impact crater in the outback"),
    dict(name="Mount Taranaki", country="New Zealand", lon=174.0634, lat=-39.2963, start=7,
         wrong=["Mount Fuji", "Mayon Volcano"], note="Ringed by the round edge of a national park"),
    dict(name="Tongariro", country="New Zealand", lon=175.6321, lat=-39.1569, start=7,
         wrong=["Mount Taranaki", "Mount Rainier"],
         note="New Zealand's first national park, a UNESCO World Heritage Site", unesco=True),
    dict(name="Milford Sound", country="New Zealand", lon=167.9200, lat=-44.6400, start=7,
         wrong=["Geirangerfjord", "Doubtful Sound"], note="Part of Te Wahipounamu, a UNESCO World Heritage Site",
         unesco=True),
    dict(name="Bora Bora", country="French Polynesia", lon=-151.7415, lat=-16.5004, start=7, wrong=["Moorea", "Aitutaki"],
         note="An island ringed by a turquoise lagoon"),

    # ---------------------------------------------------------------- 北アメリカ
    dict(name="Manhattan", country="United States", lon=-73.9654, lat=40.7829, start=4, wrong=["Chicago", "Toronto"],
         where="in New York City", note="Home to Central Park"),
    dict(name="Washington, D.C.", country="United States", lon=-77.0365, lat=38.8895, start=4,
         wrong=["Ottawa", "Philadelphia"], where="in the United States", note="Home to the National Mall"),
    dict(name="San Francisco", country="United States", lon=-122.4783, lat=37.8199, start=5,
         wrong=["Vancouver", "Seattle"], where="in California", note="Home to the Golden Gate Bridge"),
    dict(name="Grand Canyon", country="United States", lon=-112.0947, lat=36.1056, start=9,
         wrong=["Fish River Canyon", "Copper Canyon"], where="in Arizona", note=UNESCO, unesco=True),
    dict(name="Horseshoe Bend", country="United States", lon=-111.5197, lat=36.8817, start=1.8, end=30,
         wrong=["Goosenecks State Park", "Fish River Canyon"], where="in Arizona",
         note="A horseshoe-shaped bend of the Colorado River"),
    dict(name="Meteor Crater", country="United States", lon=-111.0225, lat=35.0270, start=2.5, end=30,
         wrong=["Wolfe Creek Crater", "Pingualuit Crater"], where="in Arizona",
         note="Made by a meteorite about 50,000 years ago"),
    dict(name="Crater Lake", country="United States", lon=-122.1080, lat=42.9446, start=7,
         wrong=["Lake Tahoe", "Lake Taupo"], where="in Oregon", note="The deepest lake in the United States"),
    dict(name="Mount St. Helens", country="United States", lon=-122.1944, lat=46.1914, start=6,
         wrong=["Mount Rainier", "Mount Hood"], where="in Washington State", note="Famous for its 1980 eruption"),
    dict(name="Mount Rainier", country="United States", lon=-121.7603, lat=46.8523, start=8,
         wrong=["Mount Fuji", "Mount Shasta"], where="in Washington State",
         note="The highest mountain in Washington State"),
    dict(name="Diamond Head", country="United States", lon=-157.8049, lat=21.2620, start=3, end=30,
         wrong=["Haleakalā", "Molokini"], where="in Hawaii", note="A volcanic crater next to Waikiki"),
    dict(name="Cape Cod", country="United States", lon=-70.1800, lat=42.0500, start=10, end=110,
         wrong=["Long Island", "Outer Banks"], where="in Massachusetts", note="A hook-shaped peninsula"),
    dict(name="Niagara Falls", country="Canada / United States", lon=-79.0756, lat=43.0772, start=2.5, end=30,
         wrong=["Victoria Falls", "Iguazu Falls"], where="on the border of Canada and the United States",
         note="Three waterfalls on the Niagara River"),
    dict(name="Manicouagan Reservoir", country="Canada", lon=-68.7000, lat=51.3800, start=45, end=140,
         wrong=["Lake Toba", "Crater Lake"], note="A ring-shaped lake in an ancient impact crater"),
    dict(name="Great Blue Hole", country="Belize", lon=-87.5347, lat=17.3158, start=2.5, end=40,
         wrong=["Dean's Blue Hole", "Dragon Hole"], note="Part of the Belize Barrier Reef, a UNESCO World Heritage Site",
         unesco=True),
    dict(name="Lake Atitlán", country="Guatemala", lon=-91.1900, lat=14.6900, start=9, wrong=["Lake Toba", "Lake Titicaca"],
         note="A volcanic lake ringed by three volcanoes"),
    dict(name="Panama Canal", country="Panama", lon=-79.9190, lat=9.2720, start=4, wrong=["Suez Canal", "Kiel Canal"],
         note="It connects the Atlantic and Pacific oceans"),

    # ---------------------------------------------------------------- 南アメリカ
    dict(name="Rio de Janeiro", country="Brazil", lon=-43.1566, lat=-22.9486, start=5, wrong=["Cape Town", "Hong Kong"],
         note="Its mountain-and-sea landscape is a UNESCO World Heritage Site", unesco=True),
    dict(name="Brasília", country="Brazil", lon=-47.8800, lat=-15.7940, start=12, wrong=["Canberra", "Belo Horizonte"],
         note="A planned capital and UNESCO World Heritage Site", unesco=True),
    dict(name="Manaus", country="Brazil", lon=-59.9000, lat=-3.1300, start=7, wrong=["Iquitos", "Belém"],
         note="Where the dark Rio Negro meets the sandy Solimões"),
    dict(name="Lençóis Maranhenses", country="Brazil", lon=-43.1300, lat=-2.5300, start=7,
         wrong=["Sossusvlei", "White Sands"], note="White sand dunes dotted with rainwater lagoons"),
    dict(name="Cotopaxi", country="Ecuador", lon=-78.4378, lat=-0.6810, start=7, wrong=["Chimborazo", "Mount Fuji"],
         note="One of the highest active volcanoes on Earth"),
    dict(name="Easter Island", country="Chile", lon=-109.4320, lat=-27.1830, start=3.5, end=45,
         wrong=["Pitcairn Island", "Galápagos Islands"], note="Rapa Nui National Park is a UNESCO World Heritage Site",
         unesco=True),

    # ---------------------------------------------------------------- 追加分: ヨーロッパ
    dict(name="Valletta", country="Malta", lon=14.5140, lat=35.8990, start=3, end=30, wrong=["Dubrovnik", "Rhodes"],
         note="The capital of Malta and a UNESCO World Heritage Site", unesco=True),
    dict(name="Lake Garda", country="Italy", lon=10.7000, lat=45.6000, start=12, end=80, wrong=["Lake Como", "Lake Geneva"],
         note="The largest lake in Italy"),
    dict(name="Copenhagen", country="Denmark", lon=12.5700, lat=55.6760, start=5, wrong=["Stockholm", "Oslo"],
         note="The capital of Denmark"),
    dict(name="Stockholm", country="Sweden", lon=18.0700, lat=59.3260, start=5, wrong=["Helsinki", "Copenhagen"],
         note="A capital city built on islands"),
    dict(name="Moscow", country="Russia", lon=37.6176, lat=55.7520, start=4, wrong=["Warsaw", "Riga"],
         note="The Kremlin and Red Square are a UNESCO World Heritage Site", unesco=True),
    dict(name="Budapest", country="Hungary", lon=19.0457, lat=47.5000, start=6, wrong=["Prague", "Vienna"],
         note="The banks of the Danube are a UNESCO World Heritage Site", unesco=True),
    dict(name="Lisbon", country="Portugal", lon=-9.1400, lat=38.7000, start=6, wrong=["Porto", "San Francisco"],
         note="The capital of Portugal, on the Tagus estuary"),
    dict(name="Sete Cidades", country="Portugal", lon=-25.7850, lat=37.8600, start=7, end=40,
         wrong=["Crater Lake", "Lake Atitlán"], where="in the Azores, Portugal",
         note="Twin lakes inside a volcanic crater"),
    # ---------------------------------------------------------------- 追加分: アフリカ・中東・インド洋
    dict(name="Suez Canal", country="Egypt", lon=32.3000, lat=30.5800, start=6, wrong=["Panama Canal", "Corinth Canal"],
         note="It links the Mediterranean Sea and the Red Sea"),
    dict(name="Cairo", country="Egypt", lon=31.2300, lat=30.0500, start=6, wrong=["Baghdad", "Khartoum"],
         note="Historic Cairo is a UNESCO World Heritage Site", unesco=True),
    dict(name="The Pearl-Qatar", country="Qatar", lon=51.5500, lat=25.3700, start=3.5, end=40,
         wrong=["Palm Jumeirah", "Durrat Al Bahrain"], where="in Doha, Qatar", note="An artificial island off Doha"),
    # ---------------------------------------------------------------- 追加分: アジア
    dict(name="Mumbai", country="India", lon=72.8200, lat=18.9400, start=5, wrong=["Chennai", "Karachi"],
         note="Its Victorian and Art Deco ensemble is a UNESCO World Heritage Site", unesco=True),
    dict(name="Bangkok", country="Thailand", lon=100.4920, lat=13.7500, start=5, wrong=["Ho Chi Minh City", "Yangon"],
         note="The Chao Phraya River winds through the city"),
    dict(name="Phi Phi Islands", country="Thailand", lon=98.7700, lat=7.7400, start=5, end=40,
         wrong=["El Nido", "Langkawi"], note="Islands in the Andaman Sea"),
    dict(name="Seoul", country="South Korea", lon=126.9250, lat=37.5260, start=6, wrong=["Busan", "Taipei"],
         note="The Han River flows through the city"),
    dict(name="Tokyo", country="Japan", lon=139.7528, lat=35.6852, start=4, wrong=["Osaka", "Seoul"],
         note="Home to the Imperial Palace"),
    dict(name="Kansai Airport", country="Japan", lon=135.2300, lat=34.4350, start=5, end=40,
         wrong=["Hong Kong Airport", "Chubu Centrair Airport"], where="in Osaka, Japan",
         note="An airport built on an artificial island"),
    dict(name="Mount Pinatubo", country="Philippines", lon=120.3500, lat=15.1430, start=5, wrong=["Taal Volcano", "Mount Bromo"],
         where="in the Philippines", note="Its crater lake formed after the 1991 eruption"),
    dict(name="Taal Volcano", country="Philippines", lon=120.9970, lat=14.0100, start=8, wrong=["Lake Toba", "Mount Pinatubo"],
         where="in the Philippines", note="A volcano on an island in a lake"),
    dict(name="Mount Batur", country="Indonesia", lon=115.3750, lat=-8.2420, start=7, wrong=["Mount Bromo", "Mount Rinjani"],
         where="on Bali, Indonesia", note="An active volcano inside a caldera"),
    dict(name="Lake Toba", country="Indonesia", lon=98.8700, lat=2.6600, start=25, end=120,
         wrong=["Lake Taupo", "Crater Lake"], where="on Sumatra, Indonesia",
         note="A lake inside a giant volcanic caldera"),
    # ---------------------------------------------------------------- 追加分: オセアニア
    dict(name="Canberra", country="Australia", lon=149.1300, lat=-35.2950, start=6, wrong=["Brasília", "Wellington"],
         note="A planned capital built around a lake"),
    dict(name="Hutt Lagoon", country="Australia", lon=114.2400, lat=-28.1700, start=8, end=50,
         wrong=["Lake Hillier", "Lake Retba"], where="in Western Australia", note="A pink salt lake"),
    dict(name="Lake Taupo", country="New Zealand", lon=175.9000, lat=-38.8000, start=32, end=90,
         wrong=["Lake Toba", "Crater Lake"], note="A lake that fills a supervolcano caldera"),
    dict(name="Rangitoto Island", country="New Zealand", lon=174.8600, lat=-36.7870, start=6, end=40,
         wrong=["Mount Taranaki", "Diamond Head"], where="in Auckland, New Zealand",
         note="A volcanic island in Auckland's harbour"),
    # ---------------------------------------------------------------- 追加分: 北アメリカ
    dict(name="Kīlauea", country="United States", lon=-155.2800, lat=19.4100, start=5, wrong=["Mauna Kea", "Mount Etna"],
         where="in Hawaii", note="Inside Hawaiʻi Volcanoes National Park, a UNESCO World Heritage Site", unesco=True),
    dict(name="Vancouver", country="Canada", lon=-123.1400, lat=49.3000, start=6, wrong=["Seattle", "San Francisco"],
         note="Home to Stanley Park"),
    dict(name="Chicago", country="United States", lon=-87.6200, lat=41.8800, start=6, wrong=["Toronto", "Detroit"],
         where="in Illinois", note="A city on the shore of Lake Michigan"),
    dict(name="Las Vegas", country="United States", lon=-115.1700, lat=36.1150, start=5, wrong=["Phoenix", "Dubai"],
         where="in Nevada", note="Famous for the Las Vegas Strip"),
    dict(name="Lake Tahoe", country="United States", lon=-120.0400, lat=39.0900, start=28, end=80,
         wrong=["Crater Lake", "Lake Como"], where="on the California–Nevada border", note="A large alpine lake"),
    dict(name="Great Salt Lake", country="United States", lon=-112.6000, lat=41.2200, start=25, end=120,
         wrong=["Dead Sea", "Lake Urmia"], where="in Utah",
         note="The largest salt lake in the Western Hemisphere"),
    dict(name="Grand Prismatic Spring", country="United States", lon=-110.8380, lat=44.5250, start=1.5, end=30,
         wrong=["Pamukkale", "Lake Natron"], where="in Yellowstone National Park",
         note="Yellowstone is a UNESCO World Heritage Site", unesco=True),
    dict(name="New Orleans", country="United States", lon=-90.0600, lat=29.9500, start=6, wrong=["Memphis", "St. Louis"],
         where="in Louisiana", note="Built on a bend of the Mississippi River"),
    dict(name="Miami Beach", country="United States", lon=-80.1300, lat=25.7900, start=6, wrong=["Gold Coast", "Cancún"],
         where="in Florida", note="A city on barrier islands"),
    dict(name="Key West", country="United States", lon=-81.7800, lat=24.5550, start=5, end=40,
         wrong=["Nassau", "Bermuda"], where="in Florida",
         note="The southernmost city in the contiguous United States"),
    dict(name="Cancún", country="Mexico", lon=-86.7700, lat=21.1000, start=8, wrong=["Miami Beach", "Punta Cana"],
         note="Its hotel zone lies on a long, narrow strip of sand"),
]


# 内陸の自然(山・火山・湖・クレーター・峡谷・砂漠・滝など)。街・海岸・島の形より見られにくかったので、出す割合を減らす
# (make_video.NATURE_SHARE)。島の火山(ストロンボリ・桜島など)は島の形が見えるので入れない
NATURE = {
    "mount-vesuvius", "mount-etna", "lake-como", "geirangerfjord", "mount-teide", "mount-ararat", "mount-kilimanjaro",
    "ngorongoro-crater", "victoria-falls", "sossusvlei", "the-eye-of-the-sahara", "mount-nyiragongo", "mount-damavand",
    "mount-fuji", "three-gorges-dam", "mount-bromo", "mayon-volcano", "uluru", "wolfe-creek-crater", "mount-taranaki",
    "tongariro", "milford-sound", "grand-canyon", "horseshoe-bend", "meteor-crater", "crater-lake", "mount-st-helens",
    "mount-rainier", "niagara-falls", "manicouagan-reservoir", "lake-atitlan", "lencois-maranhenses", "cotopaxi",
    "lake-garda", "sete-cidades", "mount-pinatubo", "taal-volcano", "mount-batur", "lake-toba", "hutt-lagoon",
    "lake-taupo", "kilauea", "lake-tahoe", "great-salt-lake", "grand-prismatic-spring",
}


# 寄りの写真が灰色の街並みばかりで、海岸線などの形が見えにくい街。パリ(295)・ストックホルム(394)などが、
# 海岸や川の形がはっきりした回(リスボン 1,225・ケープコッド 1,194)より見られていなかったので、出す割合を減らす
# (make_video.GREY_CITY_SHARE)
GREY_CITY = {
    "moscow", "budapest", "seoul", "tokyo", "bangkok", "cairo", "washington-d-c", "las-vegas", "shanghai", "mumbai",
}


def key(p):
    """投稿記録に使う、場所ごとの決まった名前(ゲームの回は "game-" で始まる)。"""
    if p.get("id"):
        return p["id"]
    import re
    import unicodedata
    s = unicodedata.normalize("NFKD", p["name"]).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def spoken_name(p):
    n = p["name"]
    return "the" + n[3:] if n.startswith("The ") else n


def where(p):
    return p.get("where") or f"in {p['country']}"


# ---------------------------------------------------------------- ゲームの舞台の回(2026-11-21〜)
# 有名なゲームの舞台、またはモデルになった実在の場所。make_video.GAME_EVERY 本に1本、ここから出す。
# ゲームの画面・ロゴ・キャラクターは使わず、ゲーム名を文字で書くだけ。「High Resolution」とは書かない(約10m/画素)。
# game_note は画面に出す短い文、game_desc は説明欄に書く文。どちらも、ゲームの公式の舞台設定として広く知られた事実だけ。
# GTA のように架空の街のときは「舞台」ではなく「モデルになった街」と書く。
# base を書いたものは、ふつうの回の同じ場所(中心・寄りの幅・外れの選択肢)を使う。
_GAMES = [
    dict(base="washington-d-c", game="Fallout 3 and The Division 2",
         game_note="The setting of Fallout 3 (2008) and The Division 2 (2019)",
         game_desc="Fallout 3 (2008) is set in the ruins of Washington, D.C., and The Division 2 (2019) "
                   "takes place in Washington, D.C."),
    dict(base="manhattan", game="Marvel's Spider-Man",
         game_note="The setting of Marvel's Spider-Man (2018)",
         game_desc="Marvel's Spider-Man (2018) is set in Manhattan, New York City."),
    dict(base="san-francisco", game="Watch Dogs 2",
         game_note="The setting of Watch Dogs 2 (2016)",
         game_desc="Watch Dogs 2 (2016) is set in the San Francisco Bay Area."),
    dict(base="london", game="Assassin's Creed Syndicate",
         game_note="The setting of Assassin's Creed Syndicate (2015)",
         game_desc="Assassin's Creed Syndicate (2015) is set in Victorian London."),
    dict(base="paris", game="Assassin's Creed Unity",
         game_note="The setting of Assassin's Creed Unity (2014)",
         game_desc="Assassin's Creed Unity (2014) is set in Paris during the French Revolution."),
    dict(base="istanbul", game="Assassin's Creed Revelations",
         game_note="Assassin's Creed Revelations (2011) is set here, as Constantinople",
         game_desc="Assassin's Creed Revelations (2011) is set in Constantinople, today's Istanbul."),
    dict(base="hong-kong", game="Sleeping Dogs",
         game_note="The setting of Sleeping Dogs (2012)",
         game_desc="Sleeping Dogs (2012) is set in Hong Kong."),
    dict(name="Los Angeles", country="United States", lon=-118.4695, lat=33.9850, start=5,
         wrong=["San Diego", "Sydney"], where="in California", game="Grand Theft Auto V",
         game_note="The model for Los Santos in Grand Theft Auto V (2013)",
         game_desc="Los Santos, the city of Grand Theft Auto V (2013), is based on Los Angeles. "
                   "This view is centred on Venice Beach."),
    dict(name="Miami", country="United States", lon=-80.1937, lat=25.7743, start=6,
         wrong=["Tampa", "Havana"], where="in Florida", game="Grand Theft Auto: Vice City",
         game_note="The model for Vice City in Grand Theft Auto: Vice City (2002)",
         game_desc="Vice City, the city of Grand Theft Auto: Vice City (2002), is based on Miami."),
    dict(name="Boston", country="United States", lon=-71.0656, lat=42.3550, start=5,
         wrong=["Baltimore", "Halifax"], where="in Massachusetts", game="Fallout 4",
         game_note="The setting of Fallout 4 (2015)",
         game_desc="Fallout 4 (2015) is set in and around a post-apocalyptic Boston."),
    dict(name="Chicago", country="United States", lon=-87.6278, lat=41.8820, start=5,
         wrong=["Toronto", "Cleveland"], where="in Illinois", game="Watch Dogs",
         game_note="The setting of Watch Dogs (2014)",
         game_desc="Watch Dogs (2014) is set in Chicago."),
    dict(name="Seattle", country="United States", lon=-122.3321, lat=47.6062, start=6,
         wrong=["Vancouver", "Portland"], where="in Washington State", game="The Last of Us Part II",
         game_note="Much of The Last of Us Part II (2020) takes place here",
         game_desc="Much of The Last of Us Part II (2020) takes place in Seattle."),
    dict(name="Florence", country="Italy", lon=11.2560, lat=43.7731, start=3,
         wrong=["Siena", "Bologna"], game="Assassin's Creed II",
         game_note="A main setting of Assassin's Creed II (2009)",
         game_desc="Florence is one of the main cities of Assassin's Creed II (2009)."),
    dict(name="Rome", country="Italy", lon=12.4769, lat=41.8986, start=4,
         wrong=["Milan", "Naples"], game="Assassin's Creed Brotherhood",
         game_note="The setting of Assassin's Creed Brotherhood (2010)",
         game_desc="Assassin's Creed Brotherhood (2010) is set mainly in Rome."),
    dict(name="Giza", country="Egypt", lon=31.1325, lat=29.9773, start=2, end=40,
         wrong=["Luxor", "Saqqara"], game="Assassin's Creed Origins",
         game_note="Its pyramids appear in Assassin's Creed Origins (2017)",
         game_desc="Assassin's Creed Origins (2017) is set in ancient Egypt, and the pyramids of Giza appear in the game."),
]


def _game_places():
    by_key = {key(p): p for p in PLACES}
    out = []
    for g in _GAMES:
        p = dict(by_key[g["base"]]) if "base" in g else {}
        p.pop("unesco", None)
        p.update({k: v for k, v in g.items() if k != "base"})
        p["note"] = p["game_note"]
        p["id"] = "game-" + key(p)
        out.append(p)
    return out


GAME_PLACES = _game_places()
ALL_PLACES = PLACES + GAME_PLACES
