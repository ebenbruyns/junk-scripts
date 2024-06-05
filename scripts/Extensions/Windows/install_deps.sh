#!/bin/bash

function install() {
    if flatpak list | grep -q "io.github.dosbox-staging"; then
        echo "dosbox-staging flatpak is installed"
    else
        flatpak  --user install io.github.dosbox-staging -y
        
        
    fi
    
    if flatpak list | grep -q "com.github.DOSBox"; then
        echo "DOSBox flatpak is installed"
    else
        flatpak  --user install flathub com.dosbox.DOSBox -y
    fi
    
    if flatpak list | grep -q "com.dosbox_x.DOSBox-X"; then
        echo "DOSBox-X flatpak is installed"
    else
        flatpak  --user install flathub com.dosbox_x.DOSBox-X -y
    fi
}

function uninstall() {
    if flatpak list | grep -q "io.github.dosbox-staging"; then
        echo "dosbox-staging flatpak is installed, removing"
        flatpak  --user uninstall io.github.dosbox-staging -y
    fi
    
    if flatpak list | grep -q "com.github.DOSBox"; then
        echo "DOSBox flatpak is installed, removing"
        flatpak  --user uninstall com.github.DOSBox -y
    fi
    
    if flatpak list | grep -q "com.dosbox_x.DOSBox-X"; then
        echo "DOSBox-X flatpak is installed, removing"
        flatpak  --user uninstall com.dosbox_x.DOSBox-X -y
    fi
}




if [ "$1" == "uninstall" ]; then
    echo "Uninstalling dependencies: Epic extension"
    uninstall
else
    echo "Installing dependencies: Epic extension"
    install
fi