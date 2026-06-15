# Baby Crypto

A module from [pwn.college](https://pwn.college) covering cryptography from the ground up — not just how to use it, but how it breaks. The module progresses from basic XOR operations through RSA, Diffie-Hellman, and finishes with implementing a full TLS-like secure communication protocol from scratch.

All solutions were written in Python. Below are the three challenges that required the most original thinking.

---

## Highlight 1 — Breaking XOR When the Key Is Reused

**The problem:** XOR encryption is simple and fast — you XOR each byte of your plaintext against a key byte to produce ciphertext. If you know the key, decryption is trivial: just XOR again. But one level presented two ciphertexts encrypted with the same key, without giving me the key directly.

**My thinking:** If `A XOR key = C1` and `B XOR key = C2`, then `C1 XOR C2 = A XOR B`. The key cancels out entirely. If you know something about what one of the plaintexts contains — like knowing it starts with a predictable value — you can recover the other plaintext without ever learning the key.

**The insight:** The security of XOR encryption depends entirely on the key never being reused. This is why it's called a "one-time pad" — the moment you use the same key twice, the encryption of both messages is compromised. A principle that seems obvious in hindsight but becomes viscerally clear when you exploit it yourself.

---

## Highlight 2 — Breaking AES by Controlling the Input

**The problem:** AES in ECB mode encrypts each 16-byte block of plaintext independently. The challenge had a server that would encrypt anything I sent it, with a secret value appended to my input before encrypting. I needed to recover that secret without ever being given the key.

**My thinking:** Because blocks are encrypted independently, if I can control what goes into a block alongside one byte of the secret, I can brute-force that byte. I send 15 A's — the secret's first byte slides into position 16 completing the block. I record the ciphertext. Then I try all 256 possible bytes appended to my 15 A's until one produces the same ciphertext. That matching byte is the first byte of the secret. Repeat, shifting the window one byte at a time, until the full secret is recovered.

**The insight:** ECB mode's weakness isn't in the math of AES itself — AES is strong. The weakness is architectural: encrypting blocks in isolation leaks structural information. The same plaintext block always produces the same ciphertext block, which is enough to mount this attack. This is why CBC and other chaining modes exist.

---

## Highlight 3 — Implementing a Full TLS-Like Protocol

**The problem:** The final level combined everything from the previous thirteen into one challenge: establish a shared secret using Diffie-Hellman, derive an AES key from it, present a valid RSA-signed certificate to prove identity, sign the key exchange parameters to prevent tampering, then encrypt all further communication with AES-CBC.

**My thinking:** Each piece I'd built separately now had to work together in the right order. The Diffie-Hellman exchange had to happen first to establish the key. The RSA certificate had to be signed by the trusted root key. The AES key had to be derived from the shared secret using SHA256 so both sides arrived at the same key independently. Then every subsequent message had to be padded and encrypted before sending.

**The insight:** TLS isn't magic — it's a carefully sequenced combination of well-understood primitives. Having implemented each primitive from scratch in earlier levels made the final protocol feel like assembling known pieces rather than tackling something impossibly complex. It also made clear why each piece is necessary: remove any one of them and a specific attack becomes possible.
