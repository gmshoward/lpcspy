from __future__ import print_function
import csound as cs
import sys
import decimal as dec


def translate_articulation(articulation=None):
    if articulation is None:
        return cs.Articulation.full
    elif articulation == 'staccato':
        return cs.Articulation.staccato
    elif articulation == 'legato' or articulation == 'slur':
        return cs.Articulation.legato
    else:
        return cs.Articulation.full


def process_staff(stf, section):
    """Process a staff's worth of lilypond events into
    csound.py objects. Parameters are the staff file to
    process and the section object to which we'll write the
    generated events. The staff file is generated by lilypond's
    event-listener module. Returns a csound.Track object.
    """

    time_array = {}
    articulation = None  # articulation events will modify this
    dynamics = cs.Dynamics.mf
    crescendo = 0
    slurring = False
    for line in stf:
        fields = line.split()
        when = 4.0 * dec.Decimal(fields[0])
        what = fields[1]
        if what == "note":
            pitch = fields[2]
            duration = dec.Decimal(fields[4])
            articulation = cs.Articulation.legato if slurring else None
            note = Note(when, duration, articulation=articulation, pitch=pitch)
            time_array.get(when, []).append(note)
            if articulation != 'slur':
                articulation = None  # reset for the next note
        elif what == "slur":
            if int(fields[2]) > 0:
                slurring = True
                for n in time_array[when]:
                    n.articulation = cs.Articulation.legato
            else:
                slurring = False
        elif what == "script":
            script = fields[2]
            if script == "staccato" or script == "legato":
                articulation = script
            if script == "tenuto":
                artciulation = "legato"
        elif what == "tempo":
            tempo = fields[2]
            tempo_point = cs.TempoPoint(when)


if __name__ == "__main__":
    s = Section("test section")
    with open(daFile) as f:
        t = process_staff(f, s)
