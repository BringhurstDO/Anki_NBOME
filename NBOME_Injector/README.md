# NBOME Pearl Injector (Gemini AI)

Anki add-on for **COMLEX / NBOME-focused pearls** on top of your UWorld-tagged cards. You paste UWorld question IDs; the add-on finds matching notes, calls **your** Gemini API key, and appends text to the **Extra** field (or another field you configure).

---

## BYOK setup (3 steps)

**Bring your own key** — the add-on does not ship with an API key. You pay nothing to the author; Google’s free tier / your account covers usage.

1. **Get a free Gemini API key**  
   Open **[Google AI Studio — API keys](https://aistudio.google.com/app/apikey)** (`https://aistudio.google.com/app/apikey`), sign in with Google, click **Create API key**, and copy it. (Same page linked inside the add-on’s **Config** window.)

2. **Paste it into Anki**  
   In Anki: **Tools → Add-ons** → select **NBOME Pearl Injector** → **Config**. A **settings window** opens (API key, target field, daily limit, optional **custom UWorld tag prefix** for non-standard AnKing paths). Paste your key there and click **OK**.  
   Advanced users can still use **View Files** / `meta.json` if they prefer raw JSON.

   **Daily limit (matches Google’s free tier for this model):**  
   Google’s free tier for **Gemini 2.5 Flash** currently allows **250 requests per day** (RPD) for the API tier this add-on uses—see Google’s official **[Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)** table (free tier / per-model columns) and **[pricing](https://ai.google.dev/pricing)**; limits can change without notice.

   This add-on includes a **built-in safety counter** (default **250** successful generations per day) so you are less likely to hit Google’s quota **mid-batch**. Adjust `daily_gemini_request_cap` or turn the limit off in **Tools → Add-ons → Config** if you use paid quota or prefer to manage risk only in Google’s console.

   - `limit_daily_gemini_requests`: `true` (default) enforces the cap; set to `false` to disable local blocking (**“keep running”** — only Google can then stop you via rate limits or billing).  
   - `daily_gemini_request_cap`: max **successful** Gemini calls counted per **local calendar day** on this computer (default `250`).  

   **Important:** The add-on **cannot** read Google’s remaining quota from their servers. The counter tracks only **successful pearl updates from this add-on** and resets on your device’s local midnight. Google’s own daily window may use a different timezone (their docs often describe **Pacific Time** for resets—confirm on the pages above). Counts are stored in `.nbome_gemini_usage.json` inside the add-on folder.

   **Maintainers / staying up to date:** There is **no reliable automatic way** for this add-on to pull Google’s live free-tier numbers (Google does not publish a small, stable “free RPD” endpoint meant for third-party clients). When Google changes quotas, update your **Config** `daily_gemini_request_cap` to match, and for a new release bump the defaults in `config.json` and `_DEFAULT_DAILY_CAP` in `__init__.py`. Re-check periodically: bookmark **[Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)** and your **[AI Studio](https://aistudio.google.com/)** usage.

3. **Run the tool**  
   **Tools → Inject NBOME Pearls (UWorld IDs)** → choose **deck/version** (Step 1 or 2, v11 or v12 — same idea as UWorld Batch Unsuspend) and choose **Target Source**:  
   - **UWorld Question IDs (Paste below)**: paste IDs (commas or line breaks), then run.  
   - **Today's Reviews (Due Cards)**: no ID paste needed; pulls `is:due -is:suspended` scoped to your selected deck/version tag.

---

## Scope (read this first)

This add-on is **optimized for the common AnKing Step 1 / Step 2 style layout**:

- **Card text:** reads from **`Text`** or **`Front`**, and **`Back Extra`** or **`Back`** (in that order).  
- **Duplicate Shield:** before calling Gemini for a note, the add-on checks whether the target field already contains `NBOME Pearl:`. If it does, that note is skipped (prevents duplicate pearls).
- **Universal NBOME Prompt:** Gemini is instructed to act as a **Universal NBOME Expert** and output **1–2** high-yield nuances selected from relevant domains (OMM: viscerosomatics/Chapman/Muscle Energy, Psychiatry: first-line meds + side effects, Ethics/Law: mandatory reporting/Tarasoff/minor consent, Public Health: USPSTF + CDC vaccines).
- **HTML emphasis only:** Gemini is instructed to **never use Markdown `*` for bold**. For emphasis it must use **HTML `<b>...</b>`** tags, which the add-on preserves for correct rendering on Anki mobile.
- **Finding cards (default):** for each ID, searches the **exact AnKing hierarchical tag** for the track you pick, e.g. `tag:"#AK_Step2_v12::#UWorld::Step::2857"` (Step 2 + v12 + UWorld ID `2857`). That keeps Step 1 vs Step 2 and v11 vs v12 from mixing.  
- **Today's Reviews workflow:** optional mode that processes your due unsuspended cards only, scoped to the selected deck/version tag to avoid unrelated decks.
- **Legacy mode:** optional **“tag contains ID (any deck)”** — the old broad `tag:*ID*` behavior if you need it.  
- **Custom prefix:** in **Config**, set **Custom UWorld tag prefix** to the part of the tag **before** the numeric ID (e.g. `#AK_Step2_v12::#UWorld::Step::`), then choose **Custom prefix** in the inject dialog — useful if AnKing renames tags or you use another deck’s hierarchy.

If your deck uses different field names or tag patterns, the add-on may skip notes or find nothing until you align tags/fields or adjust the track / custom prefix.

---

## Disclaimer

**AI can hallucinate. Always verify critical clinical and OMM facts.**

This tool is a study aid, not a source of truth. Confirm high-stakes detail (dosing, guidelines, OMM mappings) in trusted references.

---

## Author

Created by **Kyle Bringhurst** | Founder of SyncSOAP
