#!/bin/bash
if flatpak list | grep -q "com.github.derrod.legendary"; then
    echo "legendary flatpak is installed"
else
    cd /tmp
    wget https://github.com/ebenbruyns/legendary-flatpak/releases/download/Test-0.1/legendary.flatpak
    flatpak --user install legendary.flatpak -y
    rm legendary.flatpak
fi

if flatpak list | grep -q "io.github.dosbox-staging"; then
    echo "dosbox-staging flatpak is installed"
else
    flatpak install io.github.dosbox-staging -y
fi
echo "==================================="
echo "  Dependecy installation complete"
echo "==================================="