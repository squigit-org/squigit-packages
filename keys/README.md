# Signing Keys

Release CI publishes:

- `distribution.asc` (ASCII armored public key)
- `distribution.gpg` (binary public key)

The private key is never committed here; it is loaded from CI secrets.
