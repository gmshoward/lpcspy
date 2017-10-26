from __future__ import print_function
import csound as cs
import sys
import decimal as dec


def translate_articulation(articulation=None):
    if articulation is None:
        return cs.Articulation.full
    elif articulation == 'staccato':
        return cs.Articulation.staccato
    elif articulation == 'legato' or articulation == 'tenuto':
        return cs.Articulation.legato
    else:
        return cs.Articulation.full


def process_staff(stf, track_name, instrument):
    """Process a staff's worth of lilypond events into
    csound.py objects. Parameters are the staff file to
    process and the section object to which we'll write the
    generated events. The staff file is generated by lilypond's
    event-listener module. Returns a csound.Track object.
    """

    time_array = {}
    articulation = None  # articulation events will modify this
    dyn_envelope = []
    crescendo = 0
    slurring = False
    note = None  # last processed note
    open_ties = {}
    tempi = []
    for line in stf:
        fields = line.split()
        when = dec.Decimal(4.0) * dec.Decimal(fields[0])
        what = fields[1]
        if what == "note":
            pitch = fields[2]
            duration = dec.Decimal(4.0) * dec.Decimal(fields[4])
            if slurring:
                duration = -duration
            if (pitch in open_ties):
                note = open_ties.pop(pitch)
                note.duration = note.duration + duration
            else:
                articulation = cs.Articulation.legato if slurring else None
                note = cs.Note(when, duration, articulation=articulation, pitch=pitch)
                #time_array.get(when, []).append(note)
                if when in time_array:
                    time_array.get(when).append(note)
                else:
                    when_array = [note]
                    time_array[when] = when_array
        elif what == "slur":
            if int(fields[2]) < 0:
                slurring = True
            else:
                slurring = False
            for n in time_array[when]:
                # toggle duration sign to represent new slur state
                n.duration = -(n.duration)
        elif what == "tie":
            open_ties[note.pitch] = note
        elif what == "script":
            script = fields[2]
            articulation = translate_articulation(script)
            for n in time_array[when]:
                n.articulation = articulation
        elif what == "tempo":
            tempo = dec.Decimal(fields[2]) / dec.Decimal(4)
            tempi.append((dec.Decimal(when), dec.Decimal(tempo)))
        elif what == "rest":
            pass # nothing to do with respect to csound
        else:
            print("unknown line", fields, file=sys.stderr)

    if len(dyn_envelope) == 0:
        dynamics = cs.Dynamics.constant(cs.Dynamics.mf, absolute=True)
    else:
        dynamics = cs.Dynamics(dyn_envelope, absolute=True)
    chords = []
    when_keys = sorted(time_array.keys())
    for when in when_keys:
        when_array = time_array[when]
        notes = []
        for event in when_array:
            notes.append(event)
        chords.append(cs.Chord(notes))
    track = cs.Track(instrument, track_name, chords)
    section = cs.Section(track_name, [track], tempi, cs.decZero, dynamics)
    return section


if __name__ == "__main__":
    instrument = cs.Instrument(77)
    track_name = "test-Bass"
    daFile = track_name + ".notes"
    with open(daFile) as f:
        s = process_staff(f, track_name, instrument)
    s.emit()	

