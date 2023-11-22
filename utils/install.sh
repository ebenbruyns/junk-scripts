#!/bin/bash

chmod -R 755 ~/homebrew/plugins

mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh

~/miniconda3/bin/conda init bash
~/miniconda3/bin/conda init zsh

unzip junk-store.zip 
mv Junk\ Store ~/homebrew/plugins/junk-store
mkdir -p ~/homebrew/data/junk-store
cp -Rf ./data/* ~/homebrew/data/junk-store/
mkdir -p ~/bin
cp ./bin/* ~/bin
chmod 755 ~/bin/*.sh
cp db/*.db ~/
flatpak install io.github.dosbox-staging -y

source ~/.bashrc

eval "$(conda shell.bash hook)"
source ~/miniconda3/etc/profile.d/conda.sh
conda activate base

pip install chardet
pip install pip install legendary-gl
legendary auth

sudo systemctl restart plugin_loader
