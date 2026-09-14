# Social-Media Content-Engine — Setup-Anleitung

Automatisch generierte, faceless Kurzvideos (Instagram Reels / TikTok / YouTube
Shorts) fürs Nischenthema **Money Psychology & Financial Literacy** —
englischsprachig, kein Gesicht, keine eigene Stimme, kein manuelles
Content-Erstellen nötig. Läuft komplett kostenlos über GitHub Actions.

Getestet & lauffähig: `python scripts/generate_video.py` erzeugt aus einem
vorgeschriebenen, faktengeprüften Skript in ~30–40 Sekunden ein fertiges
1080×1920-MP4 mit animiertem Hintergrund, groß eingeblendeten Kern-Aussagen
("Kinetic Typography"), Branding und Hashtags am Ende.

## Was hier drin ist

```
content/scripts_bank.json     35 fertige, recherchierte Skripte (Startkapital)
config/niches.yaml             Nischen-Konfiguration + 2 Ausweich-Nischen
scripts/build_video.py         Video-Rendering (PIL + ffmpeg, keine externen Assets nötig)
scripts/generate_video.py      Orchestrator: nächstes Skript -> fertiges Video
poster/instagram_post.py       Auto-Posting zu Instagram Reels (Meta Graph API)
poster/tiktok_post.py          Auto-Posting/Draft zu TikTok (Content Posting API)
.github/workflows/daily-content.yml   Täglicher Cron-Job, 100% kostenlos
assets/music/                  optional: eigene MP3s hier rein, sonst automatisch generierte Musik
```

## Warum dieses Format (und diese Nische)

- **Kein Schrott:** Jedes Skript basiert auf dokumentierten
  verhaltensökonomischen Phänomenen (Anchoring, Hedonic Adaptation,
  Lifestyle Creep etc.) oder neutralen historischen Fakten — keine
  Finanzberatung, keine erfundenen Zahlen, keine Clickbait-Lügen.
- **Kein Gesicht, keine eigene Stimme:** Reiner Text-over-Animation-Stil
  ("Kinetic Typography"). Funktioniert stumm (Standard bei den meisten
  Social-Views) genauso gut wie mit Ton.
- **Nische Money Psychology:** In mehreren aktuellen Quellen (siehe
  Quellenangaben am Ende) durchgehend als eine der am besten
  monetarisierbaren faceless-Nischen genannt — großes Affiliate-Ökosystem
  (Budget-Apps, Investment-Plattformen, Kreditkarten), global evergreen,
  und lässt sich sauber faktenbasiert halten (siehe Disclaimer unten).
- **Auf Reichweite getrimmt:** Hooks in den ersten 1-2 Sekunden, Videos
  bewusst kurz gehalten (~15-25s — Algorithmen gewichten die
  Fertigschau-Rate stark), und viele CTAs sind bewusst
  Kommentar-/Save-/Share-Bait ("Comment your worst...", "Tag someone
  who...", "Save this before...") — Kommentare, Saves und Shares wiegen
  auf TikTok/Reels deutlich schwerer fürs Ausspielen als reine Likes.
  Musik läuft automatisch mit: prozedural generierte Ambient-Beds
  (ffmpeg-synthetisiert, jedes Video leicht anders), kein manuelles
  Hochladen von Tracks nötig — eigene MP3s in `assets/music/` überschreiben
  das weiterhin, falls gewünscht.

Zwei Ausweich-Nischen liegen vorbereitet in `config/niches.yaml`
("ai-tools", "curiosity-facts") — falls die Finance-Nische nicht zieht oder
du Abwechslung willst, brauchst du nur eine neue `content/<niche>_bank.json`
im selben Format wie `scripts_bank.json` zu schreiben und `active:` in
`config/niches.yaml` umzustellen.

## Schritt 1 — Lokal testen (schon erledigt, optional wiederholen)

```bash
pip install -r requirements.txt
python scripts/generate_video.py          # 1 Video
python scripts/generate_video.py --count 5   # 5 Videos auf einmal
```

Videos landen in `output/`, zusammen mit einer `.txt`-Datei (Caption +
Hashtags) pro Video.

## Schritt 2 — Auf GitHub bringen (kostenlos, ~10 Minuten)

1. Neues **privates oder öffentliches** GitHub-Repo erstellen (öffentlich ist
   einfacher fürs Hosting der Video-URLs, siehe unten — bei privatem Repo
   brauchst du stattdessen z. B. GitHub Releases + einen Token).
2. Diesen Ordner hochladen/pushen.
3. Fertig — der Workflow in `.github/workflows/daily-content.yml` läuft ab
   jetzt automatisch **3× täglich** (12, 16 und 23 Uhr UTC — auf Peak-Zeiten
   für ein US/UK-lastiges Publikum getrimmt) und erzeugt ein neues Video.
   Manuell testen: Tab "Actions" → "Daily content run" → "Run workflow".

Das allein liefert dir bereits **täglich ein fertiges Video im Repo** — auch
ganz ohne die Schritte 3/4 unten, die nur fürs *automatische Posten*
gebraucht werden. Bis dahin: Video aus `output/` selbst hochladen dauert
30 Sekunden pro Tag.

## Schritt 3 — Instagram Auto-Posting einrichten (kostenlos, einmalig)

Instagram (Meta) verlangt für automatisches Posten grundsätzlich eine
**App Review** — kostenlos, aber nicht instant. Kurzfassung:

1. Instagram-Account auf **Business oder Creator** umstellen (Instagram-App
   → Einstellungen → Konto) und mit einer Facebook-Seite verknüpfen.
2. App auf [developers.facebook.com](https://developers.facebook.com)
   erstellen, Produkt "Instagram" hinzufügen.
3. Dich selbst als Tester/Admin der App hinzufügen — damit kannst du schon
   **vor** der offiziellen Review für deinen eigenen Account testen.
4. Permission `instagram_content_publish` beantragen (App Review, kostenlos,
   meist wenige Tage). Für den Start reicht ein einfaches Nutzungsvideo:
   "Ich poste automatisiert generierte, faceless Bildungs-Reels auf meinen
   eigenen Account."
5. Long-lived Access Token + deine Instagram Business Account ID besorgen
   (Meta-Doku: "Content Publishing").
6. Beides als GitHub-Secrets speichern: Repo → Settings → Secrets and
   variables → Actions → `IG_ACCESS_TOKEN`, `IG_BUSINESS_ACCOUNT_ID`.

Danach postet der tägliche Workflow automatisch — ganz ohne dein Zutun.

## Schritt 4 — TikTok Auto-Posting einrichten (kostenlos, einmalig)

TikTok ist strenger: **unaudierte Apps können nur privat posten** (nur für
dich sichtbar, max. 5 Accounts/24h). Zwei Wege:

- **Ohne Audit (sofort nutzbar):** `poster/tiktok_post.py` schickt das Video
  standardmäßig als Entwurf in dein TikTok-Postfach — du bestätigst mit
  einem Tap in der App. Kein Setup-Aufwand außer dem Access Token.
- **Mit Audit (für echtes Vollauto-Posten):** Im
  [TikTok Developer Portal](https://developers.tiktok.com) App anlegen,
  "Content Posting API" aktivieren, den kostenlosen **Direct Post Audit**
  durchlaufen (Demo-Video + Compliance-Checkliste einreichen). Danach kannst
  du `privacy_level="PUBLIC_TO_EVERYONE"` in `poster/tiktok_post.py` setzen
  und der Workflow postet komplett ohne Tap.

Access Token als GitHub-Secret: `TIKTOK_ACCESS_TOKEN`.

## Hosting der Video-Datei (technische Notwendigkeit)

Sowohl Instagram als auch TikTok laden das Video über eine **öffentlich
erreichbare URL**, nicht per Datei-Upload. Der Workflow committet jedes neue
Video automatisch ins Repo und baut die Rohdatei-URL
(`raw.githubusercontent.com/...`) — bei einem **öffentlichen Repo**
funktioniert das ohne weiteres Zutun. Bei einem privaten Repo müsstest du
stattdessen z. B. auf GitHub Releases oder einen kostenlosen Objektspeicher
(Cloudflare R2 Free Tier) umstellen.

## Rechtliches, kurz

- Alle Skripte tragen einen Disclaimer ("educational content, not financial
  advice") in jeder Caption.
- Sobald Affiliate-Links dazukommen: In den USA/vielen Ländern ist eine
  Offenlegung Pflicht (z. B. "#ad" oder "affiliate link" in der Caption).
- Prüfe die aktuellen Monetarisierungs-Voraussetzungen direkt bei
  TikTok/Instagram/YouTube, bevor du Erwartungen an Auszahlungen aufbaust —
  Schwellenwerte (Follower, Views, Alter des Accounts) ändern sich regelmäßig.

## Quellen (Recherche-Stand September 2026)

- TikTok Content Posting API, unaudited-Client-Verhalten: [developers.tiktok.com](https://developers.tiktok.com/docs/en/content-posting-api-get-started)
- TikTok Direct-Post-Audit-Anforderungen: [outstand.so](https://www.outstand.so/docs/tiktok-audit)
- Instagram App-Review-Pflicht für Publishing-Permission: [outstand.so](https://www.outstand.so/docs/configurations/instagram)
- Faceless-Nischen mit RPM/Affiliate-Daten: [flowshorts.app](https://flowshorts.app/blog/best-faceless-tiktok-niches), [reelry.app](https://www.reelry.app/best/best-faceless-instagram-niches)
- edge-tts (optionale KI-Stimme, kostenlos, kein API-Key): [github.com/rany2/edge-tts](https://github.com/rany2/edge-tts)
- Pexels API (optional, kostenlose Stock-Videos statt generiertem Hintergrund): [pexels.com/api](https://www.pexels.com/api/)

Hinweis: Die genauen RPM-Zahlen mehrerer Blog-Quellen sind nicht offiziell
von TikTok/Meta bestätigt und schwanken stark nach Zielgruppe/Region — als
grobe Orientierung für die Nischenwahl verwendet, nicht als Zusage.
