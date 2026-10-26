# Glossary - Ginga Eiyuu Densetsu (Legend of the Galactic Heroes, SNES 1992)

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.
`tools/batches.py check` enforces the tables: a JP term in the source needs its EN form in the line.

## Rulings (docs/decisions.md)
- Honorifics kept (D1): 様 after a name -> `-sama` ("Reinhard-sama"). Titles are translated, not kept: 閣下 ->
  "Your Excellency" (address) / "His Excellency"; 提督 -> "Admiral"; ranks per the Ranks table. Name order: Western.
- Romanisation (D2): the Haikasoru novel translation, then the official anime release; else Hepburn without macrons.
  The font is ASCII only: drop diacritics (Schonkopf, Muller, Trunicht, Brunhild, Jotunheim, Konigs Tiger).
- Credits: English (D3). Abbreviations: never to fit; engine work first (D4). Graphics text: all of it (D5).
- Register: military space opera, period-drama dignity. Reinhard proud and curt; Kircheis gentle, formal ("Reinhard-sama");
  Yang lazy, wry, polite; Frederica crisp and formal; Schonkopf sardonic; Attenborough breezy; Paetta pompous;
  Oberstein cold. Narration: history-book voice, past tense ("The history of the galaxy turns another page...").

## Style rules
- Speaker prefix: JP `名前「…」` -> `Name: "..."`; when JP puts the name on its own line, keep it on its own line
  (` / ` after the name). A closing 」 with no opening in the same message stays a closing `"`.
- Punctuation: 「」 -> "...", 『』 -> '...', … / ・・・ -> `...`, ！？ -> `?!`, ー (as dash) -> `--`, fullwidth
  digits/latin -> ASCII. Numbers: digits with commas ("20,000 ships"); 万 = 10,000 (２万隻 = 20,000 ships).
- Variables: `{sub0:01}{sub0:02}` (officer + rank, JP order) -> `{sub0:02} {sub0:01}` (rank first). Never glue a
  suffix onto a variable; no a/an before one.
- `{yesno}` is the YES/NO icon pair: copy it exactly, on its own line, as the JP has it.
- Dates: 宇宙暦７９６年 -> "S.E. 796"; 帝国暦４８７年 -> "I.C. 487"; 新帝国暦１年 -> "N.I.C. 1".

## Characters - Free Planets Alliance
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ヤン / ヤン・ウェンリー | Yang / Yang Wen-li | | protagonist (Alliance); ヤン・ウェンリー in full = Yang Wen-li | Yang Wenli, Yan |
| ミラクル・ヤン | Miracle Yang | | nickname | |
| ユリアン | Julian | | Julian Mintz, Yang's ward | Yurian |
| フレデリカ | Frederica | | Frederica Greenhill, Yang's aide | Frederika |
| グリーンヒル | Greenhill | | Frederica's surname; her father Admiral Dwight Greenhill | |
| キャゼルヌ | Cazerne | | Alex Cazerne | Caselnes |
| アッテンボロー | Attenborough | | Dusty Attenborough | |
| シェーンコップ | Schonkopf | | Walter von Schonkopf, Rosen Ritter | Schenkopp, Schoenkopf |
| ラップ | Lappe | | Jean Robert Lappe, Yang's friend | Rap |
| ビュコック | Bucock | | Alexandor Bucock | Bewcock |
| メルカッツ | Merkatz | | Willibald Joachim von Merkatz (Empire, later defects) | |
| パエッタ | Paetta | | | Paeta |
| ウランフ | Uranff | | | Ulanhu |
| ボロディン | Borodin | | | |
| モートン | Morton | | | |
| ルグランジュ | Legrange | | | Le Grand |
| アル・サレム / アル．サレム | Al Salem | | | |
| アップルトン | Appleton | | | |
| ホーウッド | Hawood | | | Horwood |
| パストーレ | Pastolle | | | Pastore |
| ムーア | Moore | | | Muarr |
| ルフェーブル | Lefebvre | | | |
| フィッシャー / フイッシャー | Fischer | | Edwin Fischer | Fisher |
| グエン | Nguyen | | Nguyen Van Thieu | Guen |
| マリノ | Marino | | | |
| ストークス | Stokes | | | |
| アラルコン | Alarcon | | | |
| マリネッティ | Marinetti | | | |
| ザーニアル | Zanial | | | |
| トリューニヒト | Trunicht | | Job Trunicht (ヨブ = Job) | Truniht |
| リンチ | Lynch | | Arthur Lynch (El Facil) | Linch |
| ポプラン | Poplin | | Olivier Poplin | |
| シェリー | Sherry | | | |

## Characters - Galactic Empire
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ラインハルト | Reinhard | | Reinhard von Lohengramm (protagonist, Empire) | Rainhart |
| ローエングラム | Lohengramm | | "Duke Lohengramm" (ローエングラム公) | Lohengram |
| キルヒアイス | Kircheis | | Siegfried Kircheis; ジーク = Siegfried | Kirchheis |
| アンネローゼ | Annerose | | Reinhard's sister | |
| ミッターマイヤー | Mittermeyer | | Wolfgang Mittermeyer | Mittermeier |
| ロイエンタール | Reuenthal | | Oskar von Reuenthal | Loyenthal |
| ビッテンフェルト / ビュッテンフェルト | Bittenfeld | | Fritz Josef Bittenfeld | |
| ミュラー | Muller | | Neidhart Muller | Mueller |
| メックリンガー | Mecklinger | | | |
| ケンプ | Kempf | | | Kemp |
| ルッツ | Lutz | | | |
| ワーレン | Wahlen | | | Warren |
| アイゼナッハ | Eisenach | | | |
| ファーレンハイト / フォーレンハイト | Fahrenheit | | | |
| シュタインメッツ | Steinmetz | | | |
| レンネンカンプ | Lennenkamp | | | |
| ケスラー | Kessler | | | |
| シュターデン | Staden | | | |
| エルラッハ | Erlach | | | |
| バイエルライン | Bayerlein | | | |
| ドロイゼン | Droysen | | | |
| トゥルナイゼン | Thurneisen | | | |
| アルトリンゲン | Altringen | | | |
| ブラウヒッチ / ブラウナヒッチ | Brauchitsch | | | |
| カルナップ | Karnap | | | |
| アイヘンドルフ | Eichendorf | | | |
| パトリッケン | Patricken | | | |
| オルラウ | Orlau | | | |
| レッケンドルフ | Reckendorf | | | |
| オーベルシュタイン | Oberstein | | Paul von Oberstein | Oberstain |
| ヒルダ | Hilda | | Hildegard von Mariendorf (ヒルデガルト); フロイライン・マリーンドルフ = Fraulein Mariendorf | |
| マリーンドルフ | Mariendorf | | | |
| シュナイダー | Schneider | | Merkatz's aide | |
| ブラウンシュヴァイク / ブラウンシュベイク | Braunschweig | | Duke Braunschweig | Brunswick |
| リッテンハイム | Littenheim | | Marquis Littenheim | |
| アンスバッハ | Ansbach | | Braunschweig's retainer | |
| シャフト | Shaft | | Anton Hilmer von Shaft | |
| リヒテンラーデ | Lichtenlade | | | |
| フリードリヒ４世 | Friedrich IV | | | |
| エルウィン・ヨーゼフ | Erwin Josef | | Erwin Josef II, child emperor | |
| ルドルフ・フォン・ゴールデンバウム | Rudolf von Goldenbaum | | ゴールデンバウム王朝 = Goldenbaum dynasty | |

## Characters - Phezzan
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ルビンスキー | Rubinsky | | Adrian Rubinsky, Landesherr of Phezzan | |
| ルパート | Rupert | | Rupert Kesselring | |
| レオポルド・ラープ | Leopold Raap | | | |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| イゼルローン | Iserlohn | | 要塞 = Iserlohn Fortress | Izerlohn |
| ガイエスブルグ | Geiersburg | | Geiersburg Fortress | Geiersberg |
| フェザーン | Phezzan | | 自治領 = Dominion of Phezzan | Fezzan |
| ハイネセン | Heinessen | | Alliance capital | Heinesen |
| オーディン | Odin | | Imperial capital (主星 = capital world) | |
| アスターテ | Astarte | | | |
| アムリッツァ | Amritsar | | | Amritzer |
| エル・ファシル | El Facil | | | El Fasil |
| ヴァルハラ | Valhalla | | | |
| カストロプ | Kastrop | | | |
| ダゴン | Dagon | | | |
| ドーリア | Doria | | | |
| ヴェスターラント | Westerland | | | |
| リップシュタット | Lippstadt | | 盟約 = Lippstadt Pact; 貴族連合軍 = Lippstadt (noble) coalition forces | |
| ランテマリオ | Rantemario | | | |
| バーミリオン | Vermillion | | | Vermilion |
| バーラト | Baalat | | バーラト和約 = Baalat Treaty | Barat |
| ライガール・トリプラ | Raigal and Tripra | | two star systems | |
| タッシリ | Tassili | | | |
| アルタイル | Altair | | | |
| ラグナロック | Ragnarok | | Operation Ragnarok | |

## Ships (names.json; max = name slot, no cap since the engine change)
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ブリュンヒルト | Brunhild | | Reinhard | Brunhilde |
| バルバロッサ | Barbarossa | | Kircheis | |
| ジンロウ | Beowulf | | Mittermeyer (人狼) | Jinrou |
| トリスタン | Tristan | | Reuenthal | |
| オウコ | Konigs Tiger | | Bittenfeld (王虎) | Ouko |
| リューベック | Lubeck | | Muller | |
| クヴァシル | Kvasir | | Mecklinger | |
| ヨーツンハイム | Jotunheim | | Kempf | |
| スキールニル | Skirnir | | Lutz | |
| カリュウ | Salamander | | Wahlen (火竜) | Karyu |
| ヴィーザル | Vidar | | Eisenach | |
| アースグリム | Asgrimm | | Fahrenheit | |
| フォンケル | Fornkell | | Steinmetz | |
| ガルガ．ファルムル | Garga Falmul | | Lennenkamp | |
| ファルセティ | Forseti | | Kessler | |
| ヒューベリオン | Hyperion | | Yang | |
| レダ２ | Leda II | | | |
| リオグランデ | Rio Grande | | Bucock | |
| バンコ | Pangu | | Uranff (盤古) | Banco |
| ベルーン | Perun | | Borodin | |
| ディオメデス | Diomedes | | | |
| レオニダス / レオニダス２ | Leonidas / Leonidas II | | | |
| パラミデュース | Palamedes | | | |
| クリシュナ | Krishna | | | |
| ケツアルコアトル | Quetzalcoatl | | | |
| パトロクロス | Patroclus | | Paetta | |
| ペルガモン | Pergamon | | | |
| ク．ホリン | Cu Chulainn | | | |
| トリグラフ | Triglav | | Attenborough | |
| アガートラム | Agateram | | | |
| マウリア | Mauria | | | |
| マルドゥーク | Marduk | | | |
| ユリシーズ | Ulysses | | | |
| シバァ | Shiva | | | |
| ノーマル．タイプ | Standard Type | | generic flagship | |

## Ranks and military terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 元帥 | Fleet Admiral | | 帝国元帥 = Imperial Marshal | Marshal (Alliance) |
| 上級大将 | Senior Admiral | | Empire only | |
| 大将 | Admiral | | | |
| 中将 | Vice Admiral | | | |
| 少将 | Rear Admiral | | | |
| 准将 | Commodore | | | |
| 大佐 | Captain | | | |
| 少佐 | Lieutenant Commander | | | Major |
| 大尉 / 中尉 | Lieutenant | | | |
| 提督 | Admiral | | | |
| 総司令官 | commander-in-chief | | | |
| 司令官 | commander | | | |
| 副官 | aide | | | adjutant |
| 艦隊 | fleet | | 第１３艦隊 = 13th Fleet | |
| 分艦隊 | division | | 分艦隊司令官 = division commander | sub-fleet |
| 隻 | ships | | | |
| 同盟 / 自由惑星同盟 | Alliance / Free Planets Alliance | | | |
| 同盟軍 | Alliance forces | | side name | |
| 帝国 / 銀河帝国 | Empire / Galactic Empire | | | |
| 帝国軍 | Imperial forces | | side name | |
| 銀河帝国正統政府 | Legitimate Government of the Galactic Empire | | | |
| 救国軍事会議 | Military Congress for the Salvation of the Republic | | | |
| 統合作戦本部 | Joint Operational Headquarters | | | |
| 査問会 | board of inquiry | | | |
| ローゼンリッター | Rosen Ritter | | 隊 = the Rosen Ritter regiment | Rosenritter |
| トゥールハンマー | Thor's Hammer | | Iserlohn's main gun | Tool Hammer |
| 全艦攻撃 | All ships, attack | | battle command | |
| 宇宙暦 | S.E. | | Space Era | |
| 帝国暦 | I.C. | | Imperial Calendar | |
| 新帝国暦 | N.I.C. | | New Imperial Calendar | |

## Decisions from earlier batches
