# NBOME Pearl Injector (Gemini AI)

Anki add-on for **COMLEX / NBOME-focused pearls** on top of your UWorld-tagged cards. You paste UWorld question IDs; the add-on finds matching notes, calls **your** Gemini API key, and appends text to the **Extra** field (or another field you configure).

---

## BYOK setup (3 steps)

**Bring your own key** — the add-on does not ship with an API key. You pay nothing to the author; Google’s free tier / your account covers usage.

1. **Get a free Gemini API key**  
   Open **[Google AI Studio — API keys](https://aistudio.google.com/app/apikey)** (`https://aistudio.google.com/app/apikey`), sign in with Google, click **Create API key**, and copy it. (Same page linked inside the add-on’s **Config** window.)

2. **Paste it into Anki**  
   In Anki: **Tools → Add-ons** → select **NBOME Pearl Injector** → **Config**. You should get the **graphical settings** window (API key, target field, daily limit, custom tag prefix). If Anki shows **raw JSON** instead, fully **restart Anki** after installing/updating the add-on, and confirm the add-on folder name under `addons21` was not renamed (the folder name must match the shipped layout). You can still edit keys in JSON if you prefer.  
   Advanced users can still use **View Files** / `meta.json` if they prefer raw JSON.

   **Daily limit (matches Google’s free tier for this model):**  
   Google’s free tier for **Gemini 2.5 Flash** currently allows **250 requests per day** (RPD) for the API tier this add-on uses—see Google’s official **[Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)** table (free tier / per-model columns) and **[pricing](https://ai.google.dev/pricing)**; limits can change without notice.

   This add-on includes a **built-in safety counter** (default **250** successful generations per day) so you are less likely to hit Google’s quota **mid-batch**. Adjust `daily_gemini_request_cap` or turn the limit off in **Tools → Add-ons → Config** if you use paid quota or prefer to manage risk only in Google’s console.

   - `limit_daily_gemini_requests`: `true` (default) enforces the cap; set to `false` to disable local blocking (**“keep running”** — only Google can then stop you via rate limits or billing).  
   - `daily_gemini_request_cap`: max **successful** Gemini calls counted per **local calendar day** on this computer (default `250`).  

   **Important:** The add-on **cannot** read Google’s remaining quota from their servers. The counter tracks only **successful pearl updates from this add-on** and resets on your device’s local midnight. Google’s own daily window may use a different timezone (their docs often describe **Pacific Time** for resets—confirm on the pages above). Counts are stored in `.nbome_gemini_usage.json` inside the add-on folder.

   **Maintainers / staying up to date:** There is **no reliable automatic way** for this add-on to pull Google’s live free-tier numbers (Google does not publish a small, stable “free RPD” endpoint meant for third-party clients). When Google changes quotas, update your **Config** `daily_gemini_request_cap` to match, and for a new release bump the defaults in `config.json` and `_DEFAULT_DAILY_CAP` in `__init__.py`. Re-check periodically: bookmark **[Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)** and your **[AI Studio](https://aistudio.google.com/)** usage.

3. **Run the tool**  
   **Tools → Inject NBOME Pearls (UWorld IDs)** → choose **deck/track** (AnKing Step 1, 2, or 3 v12 — same idea as UWorld Batch Unsuspend) and choose **Target Source**:  
   - **UWorld Question IDs (Paste below)**: paste IDs (commas or line breaks), then run.  
   - **Today's Reviews (Due Cards)**: no ID paste needed; pulls `is:due -is:suspended` scoped to your selected deck/version tag.

---

## Scope (read this first)

This add-on is **optimized for the common AnKing Step 1 / Step 2 / Step 3 v12 tag layout**:

- **Card text:** reads from **`Text`** or **`Front`**, and **`Back Extra`** or **`Back`** (in that order).  
- **Duplicate shield:** new injections skip notes that already have a pearl from this add-on, or older notes that only contain plain `NBOME Pearl:` text from before replace support (so you don’t stack duplicates). Internally, new pearls are wrapped in hidden delimiters so **Replace** can update only those entries later.
- **Replace mode:** optional checkbox. If a note already has this add-on’s hidden pearl block, it **updates** that pearl; if not, it **appends a first pearl** (even when `Extra` already has other content). Very old/manual plain `NBOME Pearl:` text is not auto-overwritten.
- **Universal NBOME Prompt:** Gemini is instructed to act as a **Universal NBOME Expert** and output **1–2** high-yield nuances selected from relevant domains (OMM: viscerosomatics/Chapman/Muscle Energy, Psychiatry: first-line meds + side effects, Ethics/Law: mandatory reporting/Tarasoff/minor consent, Public Health: USPSTF + CDC vaccines).
- **HTML emphasis only:** Gemini is instructed to **never use Markdown `*` for bold**. For emphasis it must use **HTML `<b>...</b>`** tags, which the add-on preserves for correct rendering on Anki mobile.
- **Finding cards (default):** Step 1 and Step 2 v12 — for each pasted ID, searches **both** `…#UWorld::Step::<ID>` and `…#UWorld::COMLEX::<ID>` under the selected deck, then merges matches. **Step 3 v12** uses `tag:"#AK_Step3_v12::#UWorld::<ID>"` (no `Step::` / `COMLEX::` segment). Custom prefix mode uses **one** path exactly as you configure. The inject dialog **remembers** your last track until you change it (saved in add-on config); opening **Settings** also keeps that choice. Saved **v11** preset keys from older releases are treated as the matching **v12** track.
- **QID lookup report (pasted IDs only):** After a run, a **scrollable** summary (modal until you click OK) shows how many **unique** pasted IDs matched at least one note in the **selected deck/track**, and lists IDs with **no** match (wrong deck, typo, missing card, or tag mismatch — not necessarily “COMLEX vs Step”). Duplicate paste lines are merged for search and noted in the report.  
- **Today's Reviews workflow:** optional mode that processes your due unsuspended cards only, scoped to the selected deck/version tag to avoid unrelated decks.
- **Forget / unsuspend matched notes:** optional checkboxes in the inject dialog. After the same tag query used for pearls, you can reset **only suspended** matched cards to New (clears intervals/history) and/or unsuspend suspended matched cards. This uses Anki’s scheduler only (no Gemini). Order: forget first, then unsuspend. If you also inject pearls, the daily Gemini cap can still limit how many notes get pearls, but scheduling changes already applied to the full match set. Turn off “Inject NBOME pearls” to run scheduler-only batch updates without an API key.
- **Legacy mode:** optional **“tag contains ID (any deck)”** — the old broad `tag:*ID*` behavior if you need it.  
- **Custom prefix:** in **Config**, set **Custom UWorld tag prefix** to the part of the tag **before** the numeric ID (e.g. `#AK_Step2_v12::#UWorld::Step::` or `#AK_Step3_v12::#UWorld::`), then choose **Custom prefix** in the inject dialog — useful if AnKing renames tags or you use another deck’s hierarchy.

If your deck uses different field names or tag patterns, the add-on may skip notes or find nothing until you align tags/fields or adjust the track / custom prefix.

---

## Disclaimer

**AI can hallucinate. Always verify critical clinical and OMM facts.**

This tool is a study aid, not a source of truth. Confirm high-stakes detail (dosing, guidelines, OMM mappings) in trusted references.

---

## Author

Created by **Kyle Bringhurst** | Founder of SyncSOAP
