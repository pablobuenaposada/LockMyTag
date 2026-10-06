# Getting the keys out of an AirTag

LockMyTag never talks to your AirTag, it asks Apple's Find My network for the
location, to do so it needs four values for every tag:

| Field        | What it is                                                      |
| ------------ | --------------------------------------------------------------- |
| `master_key` | Private key the rolling advertisement keys are derived from      |
| `skn`        | Primary shared secret                                            |
| `sks`        | Secondary shared secret                                          |
| `paired_at`  | When the tag was paired — the clock the key rotation counts from |

The three keys are **secrets**: anyone holding them can locate your tag, and the only way to revoke them is to unpair the tag.
Treat them like passwords.

## Step 1 — Export with OpenTagViewer AirTag Exporter

Currently, the easiest way to get the necessary fields is to use the [OpenTagViewer AirTag Exporter][wizard].

It handles getting the data off Apple, which is the fiddly part, and it runs on **Windows, Linux and macOS** — no Apple hardware required.

[wizard]: https://github.com/parawanderer/OpenTagViewer/wiki/How-To:-Export-AirTags#the-export-wizard--recommended

In short:

1. Download the build for your OS from the OpenTagViewer AirTag Exporter releases page and run it.
   Your OS will warn about an unknown developer; you will have to allow it.
2. The wizard picks a route for you. On macOS 14 or older it reads the local Find
   My files and just needs your login password. Everywhere else it signs in to
   iCloud, which needs your Apple Account, a 2FA code, and your **device
   passcode** (the iPhone PIN or Mac login password).
3. Tick the tags you want and let it write the `.zip`.

Follow the wizard's own page for the current details — it is the authority here, not this file.

Two things worth knowing before you start:

- **Only the owner can export.** Tags shared with you cannot be exported.
- **Signing in registers a device** on your Apple Account, showing up as a
  MacBook Pro with a serial like `0PENTAGX####`. You can remove it afterwards at
  [account.apple.com](https://account.apple.com).

## Step 2 — Find the values in the export

The wizard's `.zip` holds decrypted Find My plists, laid out like this:

```
OwnedBeacons/<uuid>.plist               ← the keys
BeaconNamingRecord/<uuid>/<uuid>.plist  ← the name you gave the tag
OPENTAGVIEWER.yml
```

Each `OwnedBeacons/<uuid>.plist` carries one tag.
Open the file with a text editor and find the values needed:

| Plist field                      | LockMyTag    |
|----------------------------------|--------------|
| `privateKey.key.data`            | `master_key` |
| `sharedSecret.key.data`          | `skn`        |
| `secondarySharedSecret.key.data` | `sks`        |
| `pairingDate`                    | `paired_at`  |

Take the whole `privateKey` value, not a trimmed copy of it. An iPhone or Mac
tracked through Find My names its second secret `secureLocationsSharedSecret`
instead of `secondarySharedSecret`.
