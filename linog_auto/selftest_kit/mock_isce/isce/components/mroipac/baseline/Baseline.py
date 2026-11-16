"""MOCK mroipac.baseline.Baseline (linog_auto self-test only). The real one computes the perpendicular baseline of two
frames from their orbits. This one returns felix's measured values for P084 F3320 (RD3, 27 Sept 2026: the PERP_BASELINE_TOP
and _BOTTOM of pass 1's baselines/20061010_<date>.txt), differenced between the two dates, so the self-test's network
is the real one (157 pairs under -t 730 -b 1500). A date not in the table sits at 0 m.
LINOG_MOCK_BPERP="<date>:<metres>[,...]" adds metres to a date (a planted network that falls apart);
LINOG_MOCK_SHIFT="<date>:<metres>[,...]" adds metres to a date only against the reference LINOG_MOCK_SHIFT_REF (pass 2
sees other baselines than pass 1, as the real passes do by up to 0.343 m on F3320);
LINOG_MOCK_BASEFAIL raises (a planted failure);
LINOG_MOCK_BASESLEEP=<n> with LINOG_MOCK_MARK=<file>: in a run from a folder that is not a stack/pass* folder (the
frame run of pass 2), the n-th baseline writes the marker file and sleeps 60 s (a run to be stopped there)."""
import os
import time

CALLS = [0]

# date: (top, bottom) in metres, relative to 20061010
TOPBOTTOM = {
    '20061010': (0.0, 0.0),
    '20061125': (-446.7886897430296, -452.8676869999721),
    '20070528': (1903.8343008093195, 1883.9137626012741),
    '20071013': (1386.2355777636224, 1354.0569185415434),
    '20080113': (1780.158501485879, 1738.7006761481116),
    '20080228': (1966.2584155971506, 1916.5905888744435),
    '20080414': (1981.6471879310761, 1926.8241320862676),
    '20080530': (2360.1429425691153, 2304.7274422507276),
    '20080715': (1086.0413635287666, 1075.6160729947344),
    '20080830': (702.7429078805022, 726.3552588607566),
    '20081130': (297.7941586564078, 310.157259168663),
    '20090302': (942.8218772119014, 941.8146211691785),
    '20090602': (1377.6782946151477, 1371.9093741583567),
    '20090902': (748.4950768963861, 736.5882149892564),
    '20091018': (872.1622615705443, 855.2805140314389),
    '20091203': (1228.5520430040021, 1208.3955832056215),
    '20100305': (1599.9320136966517, 1565.3506734470006),
    '20100420': (1879.8128522871489, 1840.784708898377),
    '20100605': (1670.16832545308, 1630.1207394855144),
    '20100721': (1726.7191812041863, 1685.9032202488297),
    '20101021': (2045.0827887507248, 1996.305787101203),
    '20101206': (2413.0332199316704, 2360.388874853423),
    '20110121': (2559.687168364195, 2500.2939603348514),
    '20110308': (2653.5747595152934, 2586.190593323585),
}


def _value(date):
    top, bottom = TOPBOTTOM.get(date, (0.0, 0.0))
    for item in filter(None, os.environ.get('LINOG_MOCK_BPERP', '').split(',')):
        d, m = item.split(':')
        if d == date:
            top, bottom = top + float(m), bottom + float(m)
    return top, bottom


class Baseline(object):
    def configure(self):
        pass

    def wireInputPort(self, name=None, object=None):
        setattr(self, '_' + name, object)

    def baseline(self):
        if os.environ.get('LINOG_MOCK_BASEFAIL'):
            raise RuntimeError('MOCK: the baseline computation failed (planted)')
        CALLS[0] += 1
        n = os.environ.get('LINOG_MOCK_BASESLEEP')
        if n and CALLS[0] == int(n) and '/stack/pass' not in os.getcwd():
            open(os.environ['LINOG_MOCK_MARK'], 'w').write('sleeping in %s\n' % os.getcwd())
            time.sleep(60)
        rd, sd = (f.sensingStart.strftime('%Y%m%d') for f in (self._referenceFrame, self._secondaryFrame))
        rt, rb = _value(rd)
        st, sb = _value(sd)
        if rd == os.environ.get('LINOG_MOCK_SHIFT_REF'):
            for item in filter(None, os.environ.get('LINOG_MOCK_SHIFT', '').split(',')):
                d, m = item.split(':')
                if d == sd:
                    st, sb = st + float(m), sb + float(m)
        self.pBaselineTop, self.pBaselineBottom = st - rt, sb - rb
