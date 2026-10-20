# PutraBooks Storefront (putrabooks.github.io)

Public storefront and buyer-delivery site for PutraBooks, the Carousell ebook business
(`carousell.sg/u/putrabooks`). **969 books listed** — 967 active S$1 ebook listings
plus 2 sold — all delivered as PDFs after purchase.

## Repository layout

| Path | Purpose |
|---|---|
| `index.html` | Brand landing page |
| `carousell-<series>.html` | Shelf pages: all active Carousell listings, grouped into series |
| `gumroad-*.html`, `kindle-*.html`, `kobo-*.html`, `elevenreader-*.html` | Store redirect pages for other sales channels |
| `series/` | Series information pages |
| `covers/` | Book cover art (101 PNGs) |
| `samples/` | Free sample PDFs per series |
| `downloads/<hash>/` | **Buyer delivery folders** — one per book (969). See `qr/README.md` |
| `qr/` | **QR download kit** — 969 QR codes, index CSV, visual catalog. See `qr/README.md` |
| `go/` | Short-link redirect pages |
| `sitemap.xml`, `robots.txt` | Search engine setup (submitted via IndexNow) |

## The QR buyer-delivery system

Every book has a permanent, unguessable download location:

```
https://putrabooks.github.io/downloads/<hash>/<book-slug>.pdf
```

Each book's `downloads/<hash>/` folder is pre-created with:

- `qr.png` — the book's QR code, which points at that exact PDF URL
- `book-info.txt` — book title, Carousell listing, the exact required PDF filename, and instructions

The PDF itself is **not** hosted until the book sells. Nothing is public or scannable
in advance, so no credits, storage, or bandwidth are spent on unsold inventory.

### When a book sells

1. Find the book's row in [`qr/QR-INDEX.csv`](qr/QR-INDEX.csv) or in the
   [visual catalog](https://putrabooks.github.io/qr/QR-CATALOG.html) — both list title,
   Carousell URL, hash, and download URL.
2. Drop the buyer's PDF into `downloads/<hash>/` with the exact filename given in that
   folder's `book-info.txt` (always `<book-slug>.pdf`).
3. Commit and push this repository (`main`). The download URL goes live instantly.
4. Send the buyer the QR image (`qr/<book-slug>.png`, also mirrored in the delivery
   folder as `qr.png`) or the download link, in Carousell chat.

### QR kit contents (`qr/`)

- `qr/<book-slug>.png` — 969 scannable QR codes (one per book, named by slug)
- `QR-INDEX.csv` — full mapping: title, series, listing ID/URL, hash, download URL, PDF status
- `QR-CATALOG.html` — visual reference of every QR, grouped by series
- `README.md` / `README.txt` — system documentation

### Series inventory (969 books)

| Series | Listings |
|---|---|
| The Deepspace | 186 |
| The Nurone | 164 |
| The Sky and History | 157 |
| The Solar System and Earth | 141 |
| The Archetype Series | 133 |
| The Dark Mysteries (relisted) | 50 |
| Building Infrastructure of Tomorrow | 48 |
| Building of Tomorrow | 40 |
| The Prophets | 23 |
| Building Tomorrow's People | 18 |
| Other singles | 7 |
| Sold (PDFs already live) | 2 |

### Technical notes

- Hashes are unique random 12-hex values per book; URLs are unguessable, so PDFs are
  protected by obscurity of the link alone (acceptable for S$1 ebooks).
- QR codes: ISO standard, error correction level M, black-on-white; all 969 verified
  to decode exactly to their download URL.
- Generated fully offline (Python `qrcode` library) — zero AI/cloud/API credits used.
- The QR for a book never changes; the same kit serves every future buyer of that book.
- System deployed in commits `0be8c1a` (kit) and `97ab152` (delivery folders).
