#!/usr/bin/env bash
# EduScrap - Script de Instalação e Ativação dos Serviços e Timers Systemd (Item 8 e 16)
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Instalando units do EduScrap em /etc/systemd/system/..."
sudo cp "$DIR"/*.service /etc/systemd/system/
sudo cp "$DIR"/*.timer /etc/systemd/system/

echo "==> Recarregando daemon do systemd..."
sudo systemctl daemon-reload

echo "==> Habilitando e iniciando timers..."
sudo systemctl enable --now eduscrap-notify.timer
sudo systemctl enable --now eduscrap-cleanup.timer

echo "==> Status dos timers instalados:"
sudo systemctl list-timers | grep -E "eduscrap" || true
echo "==> Concluído com sucesso!"
