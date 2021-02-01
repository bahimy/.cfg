# .cfg
nix user configuration files

Setting up new machine by first adding this line to `.bashrc`

```alias config='/usr/bin/git --git-dir=$HOME/.cfg/ --work-tree=$HOME'```

Then clone repo from Gitlab to the folder:

```git clone --bare https://github.com/bahimy/.cfg.git $HOME/.cfg```

Checkout the actual content from the bare repository to your `$HOME`:

```config checkout```

The step above might fail because your `$HOME` folder might already have some stock configuration files which would be overwritten by Git. The solution is simple: back up the files if you care about them, remove them if you don't care.
Re-run the check out if you had problems:

```config checkout```

Set the flag `showUntrackedFiles` to `no` on this specific (local) repository:

```config config --local status.showUntrackedFiles no```
