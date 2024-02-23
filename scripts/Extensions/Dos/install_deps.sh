#!/bin/bash
if flatpak list | grep -q "io.github.dosbox-staging"; then
    echo "dosbox-staging flatpak is installed"
else
    flatpak --user install io.github.dosbox-staging -y
fi

if flatpak list | grep -q "com.github.DOSBox"; then
    echo "DOSBox flatpak is installed"
else
    flatpak --user  install flathub com.dosbox.DOSBox -y
fi

if flatpak list | grep -q "com.dosbox_x.DOSBox-X"; then
    echo "DOSBox-X flatpak is installed"
else
    flatpak  --user install flathub com.dosbox_x.DOSBox-X -y
fi
