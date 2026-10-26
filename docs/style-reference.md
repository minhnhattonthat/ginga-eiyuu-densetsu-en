# Style reference

Approved pilot (work/tl/pilot.out.tsv, merged in script/main.json, checked in game 2026-10-26). Match this voice.

## Voices
| Who | Voice | Example |
|---|---|---|
| Narration | history book: past tense, measured, a little grand | "Driven by its heroes, the history of the galaxy quickened its pace, sweeping up a great many people." |
| Menus / prompts | short, plain imperative or question; button names in caps as on screen | "Which fleet will you give orders to?" / "Select LOAD or NEW." |
| Reinhard | proud, curt, commanding; "we/us" for his forces, contempt for the enemy | "I will teach them the folly of opposing us!" |
| Kircheis | gentle, formal, loyal: "Reinhard-sama" | "Are you unhurt, Reinhard-sama?" |
| Yang | mild, polite, wry understatement; dislikes bluster | "If you follow me, you won't lose." |
| Paetta | pompous, rhetorical | "Let us show the enemy the strength of our forces!" |
| Frederica | crisp, formal military register | "Lieutenant Frederica Greenhill, reporting." |
| Schonkopf / Attenborough | sardonic / breezy soldiers' talk | "A drop in the bucket." |
| Oberstein | cold, clinical | |

## Pairs
- 銀河に一人の男が現れた。ルドルフ・フォン・ゴールデンバウム　彼は、人びとの英雄となった。
  -> "A man appeared in the galaxy: / Rudolf von Goldenbaum. / He became the people's hero."
- {sub0:09}をはじめ、おおくの人びとを失ったすえ、新しい惑星を見つける事ができた。
  -> "After losing many people, {sub0:09} first among them, they at last found a new planet." ({sub0:09} = Heinessen)
- これでいいですか？ / {yesno} -> "Is this all right? / {yesno}"
- Corrected: 選択をおわります　よろしいですか？ first drafted as "Selection will be finished. Is it OK?" (stiff,
  passive) -> "End your selection. Are you sure?"

## Layout
- Write each message as running prose: the build wraps it to the box. Use ` / ` only for breaks that carry meaning
  in the JP: a speaker name on its own line, a blank-line pause (` / / `), the `{yesno}` line, a list.
- The JP `{nl}` positions are only the original wrap: ignore them otherwise.
