# Repository Rules — putrabooks.github.io

This is the PUBLIC storefront and buyer-delivery site for PutraBooks. Anything
committed here is visible to the whole world, including buyers. These rules keep
it that way on purpose: everything buyer-facing is public, and nothing internal
ever lands here.

## 1. What belongs in this repo

| Allowed | Examples |
|---|---|
| Storefront pages | `index.html`, `carousell-<series>.html`, store redirect pages, `series/` |
| Public assets | `covers/`, `samples/` |
| Buyer delivery folders | `downloads/<hash>/` — only `qr.png` before sale; `<book-slug>.pdf` added after that book sells |
| Site plumbing | `sitemap.xml`, `robots.txt`, verification files, `go/` redirects |

## 2. What must NEVER be committed

- **Any book → hash mapping.** No index, catalog, CSV, spreadsheet, or list that
  pairs a book title (or slug, or Carousell listing) with a `downloads/` hash.
- **No book-info or metadata files inside delivery folders.** A delivery folder
  contains only `qr.png` (and the PDF once the book has sold). Nothing else.
- **No internal documentation.** Security reasoning, pricing strategy, credit
  notes, owner decisions, fulfillment procedures — all of that lives in the
  private repo `PutraBooks/ebook-instructions`.
- **No secrets of any kind.** API keys, tokens, passwords, personal data.
- **No full manuscripts, EPUBs, or unpublished PDFs.** Only a sold book's PDF
  goes into its delivery folder. Free samples in `samples/` are the only
  pre-sale book content allowed.

## 3. Commit message rules

Commit messages are public forever. Never pair a book title (or slug, or
listing) with its delivery hash in a commit message, branch name, or tag.
Acceptable: "Deliver PDF for sold order" — the hash and filename live in the
change itself, not described in the message.

## 4. Git history is public too

If a mapping file, book-info file, or secret is ever accidentally pushed:

1. Remove it from the tip immediately.
2. **Rewrite history** (git filter-repo) and force-push — a plain `git rm`
   commit is NOT enough; history stays readable.
3. If a secret was exposed, rotate it and report to the owner.

## 5. Documentation rules

- `README.md` describes the storefront and the buyer-facing delivery system.
  Keep it current when the structure changes.
- README content must be safe for buyers to read: describe WHAT the system is,
  never the internal reasoning, trade-offs, or operational details.
- The authoritative internal documentation (mapping kit, fulfillment runbook,
  index CSV, catalog) lives in `PutraBooks/ebook-instructions` → `QR-Delivery/`
  and `Documents/`. Reference it by repo name only — do not copy its contents
  here.

## 6. When a book sells (summary)

Look up the book's hash and exact PDF filename in the private kit's
`QR-INDEX.csv`, add the PDF as `downloads/<hash>/<file_slug>.pdf`, push `main`,
then send the buyer the folder's `qr.png` in Carousell chat. Full procedure:
`PutraBooks/ebook-instructions` → `Documents/carousell-order-fulfillment.md`.

## 7. Delivery folder invariants

- One folder per book; hash is a random 12-hex value, unique, never reused.
- The QR (`qr.png`) is RGB-mode PNG and never changes once created.
- If hashes are ever rotated, ALL unsold folders rotate together; sold books'
  folders never change (past buyers' links must keep working).
- An unsold book's PDF URL must return 404. Verify after every change.
