# Baby Server

A module from [pwn.college](https://pwn.college) where I built a fully functional HTTP server from scratch using x86-64 assembly and raw Linux syscalls — no libraries, no C, no helper functions of any kind.

The module starts simple and progressively adds complexity: creating a socket, binding to a port, listening, accepting connections, reading requests, parsing them, serving files, handling concurrency, and supporting multiple HTTP methods.

The `.s` files in this folder are my solutions. Below are the three challenges I found most technically interesting and what I learned from each.

---

## Highlight 1 — Parsing an HTTP Request in Assembly

**The problem:** Once the server could accept a connection and read raw bytes off the socket, I needed to extract the filename from an HTTP GET request. A request looks like `GET /index.html HTTP/1.1\r\n...` — I needed just the `/index.html` part, with no string functions available.

**My thinking:** In a high-level language you'd just call `split()` or use a regex. In assembly you have nothing. I needed to write my own scanner that walked through memory byte by byte, starting after the method prefix, and stopped when it hit a space or null byte. The length of that walk gives you the filename length, and you can then overwrite the trailing space with a null byte to create a proper C-style string for the `open` syscall.

**The insight:** Every "convenient" thing a programming language does for you is just code that someone wrote. Writing it yourself in assembly made me understand exactly what string parsing costs at the hardware level and why null-terminated strings work the way they do.

---

## Highlight 2 — Fork-Based Concurrency and Stack Alignment

**The problem:** Making the server handle multiple connections concurrently required using `fork()` to spawn a child process for each accepted connection. The parent closes its copy of the client socket and loops back to accept the next one. The child handles the request and exits. Simple in concept — but the implementation in assembly was surprisingly fragile.

**My thinking:** The challenge was that both parent and child share the same stack state at the moment of the fork. The server socket file descriptor was stored on the stack, and after the fork each process needs to find it at the right offset. Any push or pop that isn't perfectly mirrored on both sides of the fork causes the parent to pass a garbage file descriptor to the next `accept()` call and silently fail.

**The insight:** Concurrency bugs at the syscall level don't throw errors — they just produce wrong behavior. I learned to reason about the exact stack state at every branch point, which is a skill that carries over to debugging any multi-process or multi-threaded system.

---

## Highlight 3 — Detecting GET vs POST at the Byte Level

**The problem:** The final server level required handling both GET and POST requests on the same socket. I needed to read the request, figure out which method it was, and branch into different handling logic — again with no string comparison functions.

**My thinking:** HTTP methods are ASCII text. `G` in ASCII is decimal 71. So after reading the request into a buffer, I could load just the first byte and compare it to the number 71. If it matches, it's a GET. If not, it's a POST. One comparison, one jump.

**The insight:** Protocols are just agreed-upon byte sequences. Once you understand that, "parsing" a protocol becomes a much less mysterious problem. This also made me think differently about how real web servers work — at their core they're doing something very similar, just much faster and with more edge cases handled.
