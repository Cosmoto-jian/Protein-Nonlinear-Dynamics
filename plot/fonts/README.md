# Bundled font

Liberation Sans 2.1.5 (Regular, Bold, Italic, BoldItalic), metric-compatible with Arial, from
https://github.com/liberationfonts/liberation-fonts (release 2.1.5, `liberation-fonts-ttf-2.1.5.tar.gz`,
sha256 7191c669bf38899f73a2094ed00f7b800553364f90e2637010a69c0e268f25d0). Licence: SIL Open Font License 1.1 (`LICENSE`).

`plot/style.py` registers these files and drops any other font with the same family name, so figures are
rendered with the same glyph metrics on every platform (macOS, Linux CI) and the SVG output is reproducible.
