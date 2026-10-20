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
| `downloads/<hash>/` | **Buyer delivery folders** — one per book (969). See below |
| `go/` | Short-link redirect pages |
| `sitemap.xml`, `robots.txt` | Search engine setup (submitted via IndexNow) |

## The QR buyer-delivery system

Every book has a permanent, unguessable download location:

```
https://putrabooks.github.io/downloads/<hash>/<book-slug>.pdf
```

Each book's `downloads/<hash>/` folder contains only `qr.png` — the book's QR code,
pointing at that exact PDF URL. Folder names are random 12-hex values with **no
index, catalog, or book names anywhere on this public site**, so a buyer who scans
their QR can reach only their own book.

The PDF itself is **not** hosted until the book sells.

### When a book sells

The book → hash → URL mapping lives in the private repo
`PutraBooks/ebook-instructions` → `QR-Delivery/` (index CSV, visual catalog, and
the fulfillment runbook `Documents/carousell-order-fulfillment.md`).

1. Look up the book's hash and exact PDF filename in `QR-Delivery/QR-INDEX.csv`.
2. Add the buyer's PDF to `downloads/<hash>/` with that exact filename.
3. Commit and push `main`. The download URL goes live instantly.
4. Send the buyer the folder's `qr.png` in Carousell chat.

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
- QR codes: ISO standard, error correction level M, black on white, **RGB mode**
  (1-bit palette PNGs render black-on-black in Carousell chat); all 969 verified
  to decode exactly to their download URL.
- Generated fully offline (Python `qrcode` library) — zero AI/cloud/API credits used.
- The QR for a book never changes; the same kit serves every future buyer of that book.
- System deployed 2026-10-20 in commits `0be8c1a` (kit), `97ab152` (delivery folders),
  with mapping docs kept privately in the ebook-instructions repo.
