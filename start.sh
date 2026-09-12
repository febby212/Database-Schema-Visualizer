#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if [ ! -d "venv" ]; then
    echo "Creating venv..."
    python3 -m venv venv
    venv/bin/pip install --upgrade pip -q
    venv/bin/pip install -r requirements.txt -q
fi

source venv/bin/activate

if ! curl -fsS http://127.0.0.1:8080/api/health >/dev/null 2>&1; then
    nohup python -m uvicorn main:app --host 127.0.0.1 --port 8080 > server.log 2>&1 &
    SERVER_PID=$!

    for _ in {1..20}; do
        if curl -fsS http://127.0.0.1:8080/api/health >/dev/null 2>&1; then
            break
        fi
        if ! kill -0 "$SERVER_PID" 2>/dev/null; then
            echo "Server gagal berjalan. Lihat log: $(pwd)/server.log" >&2
            exit 1
        fi
        sleep 0.5
    done

    if ! curl -fsS http://127.0.0.1:8080/api/health >/dev/null 2>&1; then
        echo "Server tidak siap dalam 10 detik. Lihat log: $(pwd)/server.log" >&2
        exit 1
    fi
    echo "Server dijalankan dengan PID $SERVER_PID."
else
    echo "Server sudah berjalan di http://127.0.0.1:8080"
fi

if command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://127.0.0.1:8080
elif command -v open >/dev/null 2>&1; then
    open http://127.0.0.1:8080
else
    echo "Buka manual: http://127.0.0.1:8080"
fi
