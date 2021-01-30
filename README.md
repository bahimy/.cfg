# .cfg
nix user configuration files

Setting up new machine by first adding this line to `.bashrc`

```alias config='/usr/bin/git --git-dir=$HOME/.cfg/ --work-tree=$HOME'```

Then clone repo from Gitlab to the folder:

```git clone --bare https://github.com/bahimy/.cfg.git $HOME/.cfg```
