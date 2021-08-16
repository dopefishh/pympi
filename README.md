pympi version 1.70.2
====================
### Introduction
Pympi is a package that allows you to interact with [Elan][1] files and [TextGrid][2] (regular, short and binary) files.
You can create, edit and convert both formats into each other.
It includes besides all the basic functions also functions for:
- Calculating gaps and overlaps between speakers conform [Heldner and Edlund's method][3]. (Could be used to calculate floor transfers)
- Shift annotations in both directions (Could be used when due to an error all annotations are misaligned).
- Import from CLAN's chat files.
- Merge and or filter tiers (could be used to combine hands in gesture coding)
- Move tiers between elan files.
- Etc.

### Requirements
None

### Optional requirements
- [lxml][4] is used for testing.

### Documentation and downloads
Full api documentation of the current and old versions can be found on [here][5].

Pypi repository location can be found [here][6].

### Installation
#### Automatic
- From a shell run with administrator rights:
```Shell
pip install pympi-ling
```
- Or alternatively run with administrator rights:
```Shell
easy_install pympi-ling
```

*NOTE: on windows the executable might not be in $PATH.*

#### Manual
1. Download the latest version from [pypi][5]
2. Untar the file
3. From that directory run with administrator rights
```Shell
python setup.py install
```

### How to cite
```tex
@misc{pympi-1.70,
	author={Lubbers, Mart and Torreira, Francisco},
	title={pympi-ling: a {Python} module for processing {ELAN}s {EAF} and {Praat}s {TextGrid} annotation files.},
	howpublished={\url{https://pypi.python.org/pypi/pympi-ling}},
	year={2013-2021},
	note={Version 1.70}
}
```

### Authors
Mart Lubbers (mart at martlubbers.net)
and
Francisco Toreirra (francisco.torreira at mpi.nl)

and with contributions from:
sarpu, hadware, thomaskisler, mome, mimrock and xrotwang

[1]: https://tla.mpi.nl/tools/tla-tools/elan/
[2]: http://www.fon.hum.uva.nl/praat/
[3]: http://www.sciencedirect.com/science/article/pii/S0095447010000628
[4]: http://lxml.de/
[5]: http://dopefishh.github.io/pympi/
[6]: https://pypi.python.org/pypi/pympi-ling/
