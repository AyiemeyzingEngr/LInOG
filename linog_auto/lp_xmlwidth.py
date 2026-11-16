#!/usr/bin/env python3
"""lp_xmlwidth.py -- linog_auto v0.13 r2 (the ascending record 25.4, 25.6, 25-b): the one .xml width helper, an image's width
as isce2 2.6.3 loads it from its .xml, beside the fields of the file that can disagree with it.

How isce2 loads these fields (25.4; Image.py, Parser.py and Configurable.py at v2.6.3, byte for byte v2.6.4's, the package
felix's env runs, F68): an image keeps its width in one place, coordinate1's size (Image.getWidth returns coord1.coordSize);
Configurable.load writes the image's own width property, and its xmax, into a placeholder where coordinate1 goes, then makes
coordinate1 from that component's own fields, so the width property never reaches the image; with no coordinate1 it loads no
width at all. Its length is coordinate2's size in the same way (Image.getLength). The parser (Parser.py) takes a property's
name from its name attribute or its <name> tag, in lower case with single spaces (normalize_prop_name), a component's name
the same way (normalize_comp_name capitalises it: the match does not depend on case), and a property's value from its
<value> tag, a value attribute or its own text, stripped; a name given twice keeps the last (dict.update). A coordinate's
startingValue is 0 and its delta 1 when absent, its endingValue startingValue + size x delta when absent (ImageCoordinate).
isce2 writes the width property and coordinate1's size from one attribute, so an .xml isce2 wrote holds them equal; one
edited outside isce2 can hold them apart, as P448 F0280's raw_fbs_unpacked/20091111/20091111.slc.xml and its two
.xml.bak9376 copies do (the width property 9,344; coordinate1's size and endingValue and the xmax property 9,376: isce2 loads
9,376 over a 9,344-wide image).

read(path): the fields (the top-level properties width, length, xmax, xmin and file_name; coordinate1's and coordinate2's
size, startingvalue, delta and endingvalue); check(path, want=None, what=None): (width, length, problems), the width and the
length as isce2 loads them (None where it loads none) and every way the file disagrees within itself, or with want, the
width the calling gate compares with. The problems (25.6): the width property and coordinate1's size differ, or one of
them is absent; coordinate1's endingValue or the xmax property, where the file holds them, is not startingValue + size x
delta; coordinate1's size is not want (a gate that compares the width itself passes no want: verify's G6 with the shelve's
samples, reference's G17 with its other readers, topo's G3a.14 with the geometry's; igram's G17, which read no width field
of the .xml before r2, passes the geometry's). Settled at the build, the spec naming the width only: the length by the same
rule where the file holds coordinate2 (the length property against coordinate2's size, coordinate2's endingValue), since G6
and G17 read the lines from the same file; without coordinate2 the length property stands (isce2 would take the length
from the file's size). Where the width property and coordinate1's size agree, check's width is the one the readers before
r2 took from the width property (the first name="width" of the file, lp_verify.xml_int and the like). Standard library
only (Python 3.6 or later): it runs in the env's Python and in the driver's.
"""
import xml.etree.ElementTree as ET

TOL = 1e-6   # startingValue + size x delta against endingValue and xmax, relative to the larger of 1 and the value


def _norm(s):
    """isce2's lower_single_spaced: single spaces, lower case (None stays None)."""
    return None if s is None else ' '.join(str(s).split()).lower()


def _elem(node, name):
    """isce2's getPropertyElement: the attribute, else the sub-tag's text, stripped; ValueError when both are given."""
    a = node.get(name)
    t = node.find(name)
    tx = t.text.strip() if t is not None and t.text is not None else None
    if a and tx:
        raise ValueError('%r given both as an attribute and as a tag' % name)
    return a if a else tx


def _value(node):
    """isce2's getPropertyValue: the property's own text, else its value attribute or <value> tag, stripped."""
    v1 = (node.text or '').strip()
    v2 = _elem(node, 'value')
    if v1 and v2:
        raise ValueError('a value both as the property\'s text and as a value attribute or tag')
    return v1 if v1 else v2


def _props(node):
    """{normalized name: value text} of a node's own property children, a name given twice keeping the last."""
    out = {}
    for p in node.findall('property'):
        out[_norm(_elem(p, 'name'))] = _value(p)
    return out


def _num(v):
    """A field's value as a number (int when it reads as one, else float), None when absent; ValueError otherwise."""
    if v is None:
        return None
    try:
        return int(v)
    except ValueError:
        return float(v)


def read(path):
    """The fields isce2 reads for an image's extent: dict(width, length, xmax, xmin, file_name, c1, c2), c1 and c2 each
    dict(size, startingvalue, delta, endingvalue) or None when the file holds no such component. OSError when the file
    cannot be read; ValueError when it is not XML or a field is not a number."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        raise ValueError('not XML: %s' % e)
    top = _props(root)
    comps = {}
    for c in root.findall('component'):
        comps.setdefault(_norm(_elem(c, 'name')), {}).update(_props(c))   # dict.update: a component given twice merges
    out = dict(file_name=top.get('file_name'))
    for k in ('width', 'length', 'xmax', 'xmin'):
        out[k] = _num(top.get(k))
    for k, name in (('c1', 'coordinate1'), ('c2', 'coordinate2')):
        c = comps.get(name)
        out[k] = None if c is None else dict((f, _num(c.get(f))) for f in ('size', 'startingvalue', 'delta', 'endingvalue'))
    return out


def _off(a, b):
    """a and b not within TOL of each other (relative to the larger of 1 and |b|); a NaN is off."""
    return not abs(a - b) <= TOL * max(1.0, abs(b))


def _coord(c, prop, cname, pname, problems, extra=None):
    """(the size isce2 loads, as an int, or None); problems for the coordinate's own fields and the property beside it."""
    if c is None:
        return None
    s = c['size']
    if s is None:
        problems.append('%s has no size: isce2 loads no %s' % (cname, pname))
        return None
    if not (s == s and abs(s) != float('inf')) or s != int(s) or s < 1:
        problems.append('%s\'s size %r is not a whole number of samples' % (cname, s))
        return None
    s = int(s)
    start = 0 if c['startingvalue'] is None else c['startingvalue']
    delta = 1 if c['delta'] is None else c['delta']
    end = start + s * delta
    if prop is None:
        problems.append('no %s property; %s\'s size %d (the %s isce2 loads)' % (pname, cname, s, pname))
    elif not prop == s:   # whole numbers both: equal or not (a NaN is not)
        problems.append('the %s property %s, %s\'s size %d: isce2 loads %d (25.4)' % (pname, _txt(prop), cname, s, s))
    if c['endingvalue'] is not None and _off(c['endingvalue'], end):
        problems.append('%s\'s endingValue %s, not startingValue + size x delta = %s' % (cname, _txt(c['endingvalue']), _txt(end)))
    for xname, xv in (extra or ()):
        if xv is not None and _off(xv, end):
            problems.append('the %s property %s, not %s\'s startingValue + size x delta = %s' % (xname, _txt(xv), cname, _txt(end)))
    return s


def _txt(v):
    return ('%d' % v) if isinstance(v, int) or (v == v and abs(v) != float('inf') and v == int(v)) else repr(v)


def check(path, want=None, what=None):
    """(width, length, problems) of an image's .xml as isce2 2.6.3 loads it: the width coordinate1's size (None without
    coordinate1 or its size), the length coordinate2's size (the length property without coordinate2); problems, the file
    against itself and, when want is given, coordinate1's size against want (what names it: "the geometry's width"). An
    unreadable or malformed file is a problem, not an error."""
    problems = []
    try:
        f = read(path)
    except (OSError, ValueError) as e:
        return None, None, ['%s: %s' % ('unreadable' if isinstance(e, OSError) else 'malformed', e)]
    if f['c1'] is None:
        problems.append('no coordinate1: isce2 loads no width (the width property %s)' % (_txt(f['width']) if f['width'] is not None
                                                                                          else 'absent too'))
        width = None
    else:
        width = _coord(f['c1'], f['width'], 'coordinate1', 'width', problems, extra=(('xmax', f['xmax']),))
    if f['c2'] is None:
        v = f['length']
        length = int(v) if v is not None and v == v and abs(v) != float('inf') and v == int(v) else None
    else:
        length = _coord(f['c2'], f['length'], 'coordinate2', 'length', problems)
    if want is not None and width is not None and width != want:
        problems.append('coordinate1\'s size %d (the width isce2 loads), %s %s' % (width, what or 'the gate\'s width', want))
    return width, length, problems
