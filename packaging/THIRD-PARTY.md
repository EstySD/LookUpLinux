# Local package attribution and unresolved licensing

This recipe is for a local development build. The repository has no project
LICENSE: the LookUpLinux project's own license is **unspecified**. This notice
does not grant permission to redistribute the project or clear third-party rights.

## kdotool 0.3.0

Author/upstream: jinliu, https://github.com/jinliu/kdotool . Official x86_64
release archive, Apache-2.0; its actual LICENSE is installed alongside this notice.

Source: https://github.com/jinliu/kdotool/releases/download/v0.3.0/kdotool-0.3.0-x86_64-unknown-linux-gnu.tar.gz

SHA-256: `2079cc1d492b6e83e04def4d9376e34fcb36a4e3bdc637c8c2ee6fa547ce90ff`.

## Mueller 7 English-Russian dictionary

Dictionary attributed upstream to professor V. K. Mueller, seventh edition,
StarDict conversion distributed by QStarDict. Only .ifo/.idx.gz/.dict.dz are
installed; redundant plain data and swap files are excluded.

Source: https://qstardict.ylsoftware.com/files/mueller7.tar.bz2

SHA-256: `1c5e19b857eaa5fc98f77173e8baeb22cb654c407586465b4270e4286bf070ed`.

QStarDict's https://qstardict.ylsoftware.com/dictionaries.php labels the data GPL,
but this pinned archive contains no license text or precise GPL version.
https://packagehub.suse.com/packages/stardict-dic-enru-mueller7/ independently
labels its Mueller 7 distribution GPL-2.0+. That distribution statement does not
prove the exact licensing terms of every byte in this different archive.
Accordingly this recipe retains **GPL version unspecified** and an explicit
LicenseRef-Mueller7-GPL-unspecified; no precise license version or redistribution
clearance is invented. Resolve the original license grant before redistribution.

## WordNet-derived exception data

lookup/data/irregular.txt is distributed with lookup/data/NOTICE-wordnet.txt;
that upstream notice remains in the installed application data directory.
