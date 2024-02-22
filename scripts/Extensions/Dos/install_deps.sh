#!/bin/bash
if flatpak list | grep -q "io.github.dosbox-staging"; then
    echo "dosbox-staging flatpak is installed"
else
    flatpak install io.github.dosbox-staging -y
fi
echo "==================================="
echo "  Dependecy installation complete"
echo "==================================="