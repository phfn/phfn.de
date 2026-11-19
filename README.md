# phfn.de

Statische Website für [phfn.de](https://phfn.de), gebaut mit [Hugo](https://gohugo.io).
Kein WordPress, keine Datenbank, keine externen Theme- oder CDN-Abhängigkeiten.

## Installation

Hugo (Extended) installieren: <https://gohugo.io/installation/>

## Lokal ansehen

```sh
hugo server
```

Danach <http://localhost:1313> öffnen.

## Veröffentlichen

```sh
hugo --gc --minify
```

Der fertige statische Export liegt in `public/` und kann auf einen beliebigen
Webspace hochgeladen werden (GitHub Pages, Netlify, Cloudflare Pages, eigener Server, …).

## Inhalte bearbeiten

Alle Texte liegen als Markdown in `content/`:

| Datei                        | Seite                       |
| ---------------------------- | --------------------------- |
| `content/_index.md`          | Startseite                  |
| `content/impressum/index.md` | Impressum (`/impressum/`)   |
| `content/datenschutz/index.md` | Datenschutz (`/datenschutz/`) |

Menüpunkte stehen in `hugo.toml` unter `[[menus.main]]`.
Das Profilbild liegt in `static/images/profilbild.jpg`.

## Aufbau

- `layouts/` – wenige kleine Hugo-Templates
- `assets/css/main.css` – das gesamte Styling
- `static/` – Bilder und sonstige statische Dateien

Es gibt bewusst kein JavaScript, kein Kontaktformular und keine externen Schriften.
