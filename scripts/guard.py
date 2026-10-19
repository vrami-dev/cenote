"""Refuse to start a model while another one is serving: each of the three needs most of a 24 GB GPU and 128 GB RAM."""
import socket
import sys

PORTS = {8080: "Swift / Qwen (Strata)", 8090: "GLM (Project Maya)", 8150: "DeepSeek (Xolotl)"}
busy = [f"{name} on port {port}" for port, name in PORTS.items() if socket.socket().connect_ex(("127.0.0.1", port)) == 0]
if busy:
    print("Another model is running: " + ", ".join(busy) + ". Stop it first: python scripts\\stop-all.py")
    sys.exit(1)
