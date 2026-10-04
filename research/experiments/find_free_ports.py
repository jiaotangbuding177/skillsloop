#!/usr/bin/env python3
"""Find free TCP ports in 8180-8199 for the 267/268 relays."""
import socket

free = []
for port in range(8180, 8200):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        free.append(port)
    except OSError:
        pass
    finally:
        s.close()
print("free ports:", free[:6])
