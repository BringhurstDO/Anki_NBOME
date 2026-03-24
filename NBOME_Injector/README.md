# NBOME Pearl Injector (Gemini AI)

Anki add-on for **COMLEX / NBOME-focused pearls** on top of your UWorld-tagged cards. You paste UWorld question IDs; the add-on finds matching notes, calls **your** Gemini API key, and appends text to the **Extra** field (or another field you configure).

---

## BYOK setup (3 steps)

**Bring your own key** — the add-on does not ship with an API key. You pay nothing to the author; Google’s free tier / your account covers usage.

1. **Get a free Gemini API key**  
   Open [Google AI Studio](https://aistudio.google.com/apikey), sign in, and create an API key.

2. **Paste it into Anki**  
   In Anki: **Tools → Add-ons** → select **NBOME Pearl Injector** → **Config**. A **settings window** opens (API key field, target field, daily-limit checkbox, and max requests per day). Paste your key there and click **OK**.  
   Advanced users can still use **View Files** / `meta.json` if they prefer raw JSON.

   **Daily limit (matches Google’s free tier for this model):**  
   Google’s free tier for **Gemini 2.5 Flash** currently allows **250 requests per day** (RPD) for the API tier this add-on uses—see Google’s official **[Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)** table (free tier / per-model columns) and **[pricing](https://ai.google.dev/pricing)**; limits can change without notice.

   This add-on includes a **built-in safety counter** (default **250** successful generations per day) so you are less likely to hit Google’s quota **mid-batch**. Adjust `daily_gemini_request_cap` or turn the limit off in **Tools → Add-ons → Config** if you use paid quota or prefer to manage risk only in Google’s console.

   - `limit_daily_gemini_requests`: `true` (default) enforces the cap; set to `false` to disable local blocking (**“keep running”** — only Google can then stop you via rate limits or billing).  
   - `daily_gemini_request_cap`: max **successful** Gemini calls counted per **local calendar day** on this computer (default `250`).  

   **Important:** The add-on **cannot** read Google’s remaining quota from their servers. The counter tracks only **successful pearl updates from this add-on** and resets on your device’s local midnight. Google’s own daily window may use a different timezone (their docs often describe **Pacific Time** for resets—confirm on the pages above). Counts are stored in `.nbome_gemini_usage.json` inside the add-on folder.

   **Maintainers / staying up to date:** There is **no reliable automatic way** for this add-on to pull Google’s live free-tier numbers (Google does not publish a small, stable “free RPD” endpoint meant for third-party clients). When Google changes quotas, update your **Config** `daily_gemini_request_cap` to match, and for a new release bump the defaults in `config.json` and `_DEFAULT_DAILY_CAP` in `__init__.py`. Re-check periodically: bookmark **[Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)** and your **[AI Studio](https://aistudio.google.com/)** usage.

3. **Run the tool**  
   **Tools → Inject NBOME Pearls (UWorld IDs)** → enter IDs (commas or line breaks) → wait for the progress bar → done.

---

## Scope (read this first)

This add-on is **optimized for the common AnKing Step 2 / Level 2 style layout**:

- **Card text:** reads from **`Text`** or **`Front`**, and **`Back Extra`** or **`Back`** (in that order).
- **Finding cards:** uses Anki search `tag:*<UWorld ID>*` for each ID you enter (same idea as tagging notes with the question number).

If your deck uses different field names or tag patterns, the add-on may skip notes or find nothing until you align tags/fields or adjust config.

---

## Disclaimer

**AI can hallucinate. Always verify critical clinical and OMM facts.**

This tool is a study aid, not a source of truth. Confirm high-stakes detail (dosing, guidelines, OMM mappings) in trusted references.

---

## Author

Created by **Kyle Bringhurst** | Founder of SyncSOAP
