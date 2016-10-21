from __future__ import print_function

import matplotlib.pyplot as plt
import math


# Library of musical representations for use with CSound.

# Note      (start time, duration, amplitude, pitch; legato/stoccato/duration? defer to Gesture?)
# Chord     (multiple simultaneous notes)
# Gesture   (recursive? legato/stoccato?)
# Track     (instr number, pitch map)
# Group
# Section
# Song




# "Dynamic Point"
class DP(object):
    def __init__(self, level, duration):
        self.level = float(level)
        self.duration = float(duration)


class Dynamics(object):
    """
    A Dynamics object describes amplitude over the life of a Gesture, Chord
    or Note. It can be absolute, but often expresses an amplitude offset
    from its parent Gesture or Track. Envelopes are expressed as a series
    of pairs: level, length, level, length, etc. The level element is a fraction
    of fdbs (therefore in the range [0, 1)). The length element is a fraction
    of the associated event's duration. Ordinarily all length elements should
    add up to 1, but they will all be normalized to this range in any case.
    """

    silent = 0.0
    ppp = 0.1
    pp = 0.2
    p = 0.3
    mp = 0.4
    mf = 0.5
    f = 0.6
    ff = 0.7
    fff = 0.8

    def __init__(self, envelope=[(0., 1.), (0., 0.)], absolute=False):
        self.envelope = []
        for point in envelope:
            dp = DP(point[0], point[1])
            self.envelope.append(dp)
        self.absolute = absolute
        self.normalize()

    @classmethod
    def constant(cls, level, absolute=False):
        return cls([(level, 1.0), (level, 0.0)], absolute)

    @classmethod
    def accent(cls, level=0.1):
        return cls([(level, 1.0), (level, 0.0)], False)

    def normalize(self):
        total_length = 0.0
        highest_level = 0.0
        for dp in self.envelope:
            if dp.duration < 0.0:
                raise ValueError("negative length not allowed")
            total_length = total_length + dp.duration
            absolute_level = math.fabs(dp.level)
            if (absolute_level > highest_level):
                highest_level = absolute_level

        envelope_length = len(self.envelope)
        for i in range(envelope_length):
            dp_old = self.envelope[i]
            if (highest_level == 0):
                new_level = 0
            elif (highest_level > 1.0):
                new_level = dp_old.level / float(highest_level)
            else:
                new_level = dp_old.level
            new_length = dp_old.duration / float(total_length)
            self.envelope[i] = DP(new_level, new_length)

    def initial_level(self):
        return self.envelope[0].level

    def final_level(self):
        return self.envelope[-1].level

    def average_level(self):
        level = 0.0
        dp_prev = self.envelope[0]
        for dp in self.envelope[1:]:
            segment_average = (dp_prev.level + dp.level) / 2.0
            level += (segment_average * dp_prev.duration)
            dp_prev = dp

        return level

    def slice(self, start, duration):
        if duration > 1.0 or start > 1.0:
            raise ValueError("slice parameters should be fractions")
        if duration < 0.0 or start < 0.0:
            raise ValueError("negative slice parameters not allowed")
        slice_end_time = start + duration
        if slice_end_time > 1.0:
            duration = 1.0 - float(start)

        # find slice
        envelope_length = len(self.envelope)
        slice_envelope = []
        dp_a = self.envelope[0]
        segment_start_time = 0.
        segment_end_time = dp_a.duration

        # leftmost element
        for i in range(1, envelope_length):
            dp_b = self.envelope[i]
            if segment_end_time >= start:
                break
            dp_a = dp_b
            segment_start_time = segment_end_time
            segment_end_time = segment_end_time + dp_a.duration

        initial_level_slope = (dp_b.level - dp_a.level) / dp_a.duration
        initial_time_offset = start - segment_start_time
        initial_level = (initial_level_slope * initial_time_offset) + dp_a.level
        initial_duration = min((segment_end_time - start), duration)

        slice_envelope.append((initial_level, initial_duration))

        # middle elements
        for i in range(i, envelope_length):
            dp_b = self.envelope[i]
            if segment_end_time >= slice_end_time:
                break
            slice_envelope.append((dp_b.level, dp_b.duration))
            # print slice_envelope
            dp_a = dp_b
            segment_start_time = segment_end_time
            segment_end_time = segment_end_time + dp_a.duration

        # rightmost element
        final_level_slope = (dp_b.level - dp_a.level) / dp_a.duration
        final_time_offset = slice_end_time - segment_start_time
        final_level = (final_level_slope * final_time_offset) + dp_a.level

        # update last duration
        (prev_level, prev_duration) = slice_envelope.pop()
        slice_envelope.append((prev_level, min(prev_duration, final_time_offset)))
        slice_envelope.append((final_level, 0))

        return Dynamics(slice_envelope, self.absolute)

    def add(self, addend):
        if (self.absolute and addend.absolute):
            raise ValueError("cannot add two absolute dynamics descriptors")
        if (addend.absolute):
            base = addend.envelope
            mod = self.envelope
        else:
            base = self.envelope
            mod = addend.envelope

        self.dump()
        addend.dump()
        sum_env = []

        """
        take a base segment (i.e. two points)
        calculate its slope
        if its first endpoint matches a mod point
            add their levels together
            append to the final point list
        for any mod points within the base segment
            calculate base level at that point
            add to the mod level
            append to the final point list
        if segment's final endoint matches a mod point
            add their levels together
            append to the final point list
        else
            find the associated mod segment
            calculate mod level at that point
            add base and mod levels
            append to the final point list

        """
        dp_base_a = base[0]
        base_segment_start = 0.
        base_segment_end = dp_base_a.duration
        base_point_count = len(base)

        for i_base in range(1, base_point_count):
            dp_base_b = base[i_base]
            base_segment_slope = (dp_base_b.level - dp_base_a.level) / dp_base_a.duration

            dp_mod_a = mod[0]
            mod_segment_start = 0.
            mod_segment_end = dp_mod_a.duration
            mod_point_count = len(mod)

            for i_mod in range(1, mod_point_count):
                dp_mod_b = mod[i_mod]
                mod_segment_slope = (dp_mod_b.level - dp_mod_a.level) / dp_mod_a.duration

                if (mod_segment_start >= base_segment_end):
                    # past the end of the base segment; go to next base segment
                    break

                if (mod_segment_start == base_segment_start):
                    # beginning of mod segment coincides with beginning of base segment;
                    # just add the two levels together
                    sum_point = (dp_base_a.level + dp_mod_a.level, base_segment_start)
                    sum_env.append(sum_point)

                elif (mod_segment_start > base_segment_start):
                    # mod segment begins inside base segment; calculate the immediate
                    # base level and add it to the mod level
                    base_segment_offset = mod_segment_start - base_segment_start
                    base_segment_level = (base_segment_slope * base_segment_offset) + dp_base_a.level
                    sum_point = (base_segment_level + dp_mod_a.level, mod_segment_start)
                    sum_env.append(sum_point)

                elif (mod_segment_end > base_segment_start):
                    # current mod segment overlaps the beginning of the base segment;
                    # calculate the immediate mod level and add it to the base level
                    mod_segment_offset = base_segment_start - mod_segment_start
                    mod_segment_level = (mod_segment_slope * mod_segment_offset) + dp_mod_a.level
                    sum_point = (dp_base_a.level + mod_segment_level, base_segment_start)
                    sum_env.append(sum_point)

                else:
                    # haven't reached base segment yet; keep iterating
                    pass

                # set up for next iteration
                dp_mod_a = dp_mod_b
                mod_segment_start = mod_segment_end
                mod_segment_end = mod_segment_end + dp_mod_a.duration

            # set up for next iteration
            dp_base_a = dp_base_b
            base_segment_start = base_segment_end
            base_segment_end = base_segment_end + dp_base_a.duration

        # the end of the envelopes are a special case
        sum_point = (base[-1].level + mod[-1].level, 1.0)
        sum_env.append(sum_point)

        # convert absolute times to durations
        dur_env = []
        sum_point_count = len(sum_env)
        sum_point_a = sum_env[0]

        for i_sum in range(1, sum_point_count):
            sum_point_b = sum_env[i_sum]
            sum_level = sum_point_a[0]
            if (sum_level > 1.0):
                sum_level = 1.0
            elif (sum_level < 0.0):
                sum_level = 0.0
            dur_point = (sum_level, (sum_point_b[1] - sum_point_a[1]))
            dur_env.append(dur_point)

            sum_point_a = sum_point_b

        # last point (zero duration)
        sum_level = sum_point_a[0]
        if (sum_level > 1.0):
            sum_level = 1.0
        elif (sum_level < 0.0):
            sum_level = 0.0
        dur_point = (sum_level, 0.)
        dur_env.append(dur_point)

        return Dynamics(dur_env, self.absolute or addend.absolute)

    def plot(self):
        if self.absolute:
            axes_spec = [0., 1., 0., 1.]
        else:
            axes_spec = [0., 1., -1., 1.]

        levels = []
        times = []
        current_time = 0.
        for dp in self.envelope:
            levels.append(dp.level)
            times.append(current_time)
            current_time = current_time + dp.duration
        plt.plot(times, levels)
        plt.ylabel('level')
        plt.axis(axes_spec)
        plt.show()

    def dump(self):
        pair_env = [(dp.level, dp.duration) for dp in self.envelope]
        if (self.absolute):
            abs_string = "Absolute "
        else:
            abs_string = "Relative "

        print("{0} {1}".format(abs_string, pair_env))


class Articulation:
    """
    An Articulation is a hint to a note (or group of notes) about how to
    articulate the event-- i.e., normal, stoccato, or legato.
    """
    full, staccato, legato = range(3)


class Song(object):
    """
    A Song consists of one or more Sections executed sequentially. It has no notion
    of tempo, leaving that to each Section. It provides the per-file boilerplate
    for the score.
    """

    def __init__(self, name="song name", composer="composer", sections=[]):
        self.name = name
        self.composer = composer
        self.sections = sections

    def emit(self):
        print(";;======================================================================")
        print(";; {0}".format(self.name))
        print(";; by {0}".format(self.composer))
        print(";;======================================================================")
        for section in self.sections:
            section.emit()


class Section(object):
    """
    A Section is a thematically-related set of Tracks or track Groups. It has an
    optional tempo arc and an optional dynamic arc. For now the tempi are given
    as a list of pairs of (timepoint, tempo) that can be fed more or less directly
    into a csound "t" score statement.
    """

    def __init__(self, name="song section", parts=[], tempo=[(0., 60.)], start=0., dynamics=Dynamics()):
        self.name = name
        self.parts = parts
        self.tempo = tempo
        self.start = start
        self.dynamics = dynamics
        self.duration = 0.
        for part in self.parts:
            if part.duration > self.duration:
                self.duration = part.duration

    def emit(self):
        print("\n;;======================================================================")
        print(";; {0}".format(self.name))
        tempo_statement = "\nt"
        for t in self.tempo:
            tempo_statement = tempo_statement + " {0} {1}".format(t[0], t[1])
        print(tempo_statement)

        for part in self.parts:
            part.emit(self.start, self.dynamics)
        print("\ns")


class Group(object):
    """
    A Group is a set of related Tracks. An example might be a melody Track and
    an effects Track that accompanies it. A group can have a shared dynamic arc.
    """

    def __init__(self, name="track group", tracks=[], start=0., dynamics=Dynamics()):
        self.name = name
        self.tracks = tracks
        self.start = start
        self.dynamics = dynamics
        self.duration = 0.
        for track in self.tracks:
            if track.duration > self.duration:
                self.duration = track.duration

    def emit(self, start, dynamics=Dynamics()):
        print("\n;;----------------------------------------------------------------------")
        print(";; {0}".format(self.name))
        if (not self.dynamics.absolute and dynamics.absolute):
            calc_dynamics = self.dynamics.add(dynamics)
        else:
            calc_dynamics = self.dynamics
        group_start = self.start + start
        for track in self.tracks:
            track.emit(group_start, calc_dynamics)


class Track(object):
    """
    A Track is a series of musical Events. It has a start time; duration is
    determined by the Events included. Optional dynamic arc. The track also
    stores a reference to the Instrument used to emit CSound events.
    """

    def __init__(self, instr, name=None, events=[], start=0., dynamics=Dynamics()):
        self.instr = instr
        self.events = events
        self.start = start
        self.dynamics = dynamics
        self.duration = 0.
        for event in self.events:
            self.duration += event.duration
        if name == None:
            self.name = "Instrument #{0}".format(self.instr.i_number)
        else:
            self.name = name

    def emit(self, start, dynamics=Dynamics()):
        print("\n;; {0}\n;;".format(self.name))
        if (not self.dynamics.absolute and dynamics.absolute):
            calc_dynamics = self.dynamics.add(dynamics)
        else:
            calc_dynamics = self.dynamics

        track_start = self.start + start
        event_start = track_start
        for event in self.events:
            slice_start = (event_start - track_start) / self.duration
            slice_duration = event.duration / self.duration
            passed_dynamics = calc_dynamics.slice(slice_start, slice_duration)
            event.emit(instr, event_start, passed_dynamics)
            event_start = event_start + event.duration


class Event(object):
    """
    An Event is the base class for a Gesture, Chord or Note.
    """

    def __init__(self, start=0., duration=0., dynamics=Dynamics(), articulation=None):
        self.start = start
        self.dynamics = dynamics
        self.articulation = articulation
        self.duration = duration

    def emit(self, instr, start, dynamics):
        # override me
        return None


class TempoPoint(Event):
    """
    A TempoPoint is simply a mark indicating that the section's tempo
    should have a certain value at a certain time.
    """

    def __init__(self, start=0.):
        super(TempoPoint, self).__init__(start)


class Gesture(Event):
    """
    A Gesture is a series of notes, chords, and/or Gestures. It can have a
    dynamic arc, and optional articulation (e.g. legato, staccato). It will
    have a start time and a duration (or, optionally, its duration may simply
    be the duration of its consituent elements).
    """

    def __init__(self, events=[], start=0., duration=None,
                 dynamics=Dynamics(), articulation=None):

        self.events = events

        if (duration is None):
            _duration = 0
            for event in self.events:
                _duration += event.duration
        else:
            _duration = duration

        super(Gesture, self).__init__(start, _duration, dynamics, articulation)
        # Event.__init__(self, start, _duration, dynamics, articulation)

    def emit(self, instr, start=0., dynamics=Dynamics(), articulation=None):
        if (self.articulation == None):
            passed_articulation = articulation
        else:
            passed_articulation = self.articulation

        if (not self.dynamics.absolute and dynamics.absolute):
            calc_dynamics = self.dynamics.add(dynamics)
        else:
            calc_dynamics = self.dynamics

        gesture_start = self.start + start
        event_start = gesture_start
        portamento = None  # at the beginning of the Gesture
        for event in self.events:
            slice_start = (event_start - gesture_start) / self.duration
            slice_duration = event.duration / self.duration
            passed_dynamics = calc_dynamics.slice(slice_start, slice_duration)
            portamento = event.emit(instr, event_start, passed_dynamics, passed_articulation, portamento)
            event_start = event_start + event.duration


class Chord(Event):
    """
    A chord is a set of Notes, Chords or Gestures that sound simultaneously. They may have a
    dynamic arc, a start time, a duration, and an articulation.
    """

    def __init__(self, events=[], start=0., duration=None,
                 dynamics=Dynamics(), articulation=None):

        self.events = events
        if duration is None:
            _duration = 0.0
            for event in self.events:
                if event.duration > _duration:
                    _duration = event.duration
        else:
            _duration = duration

        super(Chord, self).__init__(start, _duration, dynamics, articulation)

    def emit(self, instr, start=0., dynamics=Dynamics(), articulation=None):
        if self.articulation is None:
            passed_articulation = articulation
        else:
            passed_articulation = self.articulation

        if (not self.dynamics.absolute) and dynamics.absolute:
            calc_dynamics = self.dynamics.add(dynamics)
        else:
            calc_dynamics = self.dynamics

        if self.start is None:
            _start = start
        else:
            _start = self.start + start

        for event in self.events:
            event.emit(instr, self.start + start, calc_dynamics, passed_articulation)


class Note(Event):
    """
    A note has a start time, a duration, a dynamic arc (often a simple ampltiude),
    and an optional frequency arc (often a simple pitch).
    """

    def __init__(self, start=0.0, duration=0.0, dynamics=Dynamics(), articulation=None, pitch=None):
        self.pitch = pitch
        super(Note, self).__init__(start, duration, dynamics, articulation)

    def emit(self, instr, start=0.0, dynamics=Dynamics(), articulation=None, portamento=None):
        if self.articulation is None:
            passed_articulation = articulation
        else:
            passed_articulation = self.articulation

        if not self.dynamics.absolute and dynamics.absolute:
            calc_dynamics = self.dynamics.add(dynamics)
        else:
            calc_dynamics = self.dynamics

        if self.start is None:
            _start = start
        else:
            _start = self.start + start

        return instr.emit(_start, self.duration, calc_dynamics, passed_articulation, self.pitch, portamento)


class Instrument(object):
    """
    Subclass Instrument, overriding its basic emit function to correctly
    interpret start times, durations, dynamics and articulation into
    csound parameters.
    """

    def __init__(self, i_number):
        self.i_number = i_number

    def emit(self, start, duration, dynamics, articulation, pitch, portamento):
        params = [self.i_number]
        params = params + self.time_params(start, duration, articulation)
        params = params + self.dynamic_params(dynamics, articulation, portamento)
        params = params + self.pitch_params(pitch, articulation, portamento)

        event_line = "i"
        for p in params:
            event_line += " {0}".format(p)
        print(event_line)

        return self.update_portamento(params, articulation, portamento)

    def time_params(self, start, duration, articulation):
        if (articulation == Articulation.staccato):
            # naive way to interpret staccato articulation
            duration = 0.5 * duration
        return [start, duration]

    def dynamic_params(self, dynamics, articulation, portamento):
        # Only allow for one dynamics parameter in this base instrument.
        # More complex dynamic interpretations can be implemented in a descendant class.
        return [dynamics.average_level()]

    def pitch_params(self, pitch, articulation, portamento):
        # Just a single pitch parameter. A more complex instrument might
        # implement a previous-pitch parameter as well, derived from the
        # contents of the portamento cookie.
        if (pitch != None):
            return [pitch]
        else:
            return []

    def update_portamento(self, params, articulation, portamento):
        # This basic instrument returns previous pitch as the portamento cookie,
        # but it's not actually used.
        if (articulation == Articulation.legato):
            return params[4]
        return None


if __name__ == "__main__":
    import pprint

    d1 = Dynamics.constant(0.5, True)
    d2 = Dynamics()
    d3 = Dynamics([(0.25, 1), (0.6, 1), (0.5, 1), (0.15, 0)], True)
    d4 = Dynamics([(0.15, 1), (-0.7, 0)])
    d5 = Dynamics([(-0.17, 1), (0.2, 1), (0.1, 1), (0.05, 1), (-0.1, 0)])
    d6 = d5.add(d3)
    d6.dump()

    d3_slice = d3.slice(0.2, 0.6)
    d4_slice = d4.slice(0.2, 0.6)

    # d1.plot()
    # d2.plot()
    # d3.plot()
    # d3_slice.plot()
    # d4.plot()
    # d4_slice.plot()
    # d5.plot()
    # d6.plot()

    instr = Instrument(101)
    g1 = Gesture([
        Note(None, 1.5, Dynamics.constant(0.6, True), None, 8.07),
        Note(None, 0.5, Dynamics.constant(0.45, True), None, 8.00),
        Note(None, 0.5, d3, None, 7.07),
        Note(None, 1.25, d6, None, 8.00)
    ])
    c1 = Chord([
        g1,
        Note(None, 3.5, Dynamics([(0.5, 1), (0.25, 0)], True), Articulation.full, 7.00)
    ])
    t1 = Track(instr, "Sample Track 1", [c1, g1])

    fx = Instrument(102)
    t1_fx = Track(fx, "Effects for Sample Track 1", [
        Note(0, 15, Dynamics([(0.4, 0.2), (0.25, 0.8), (0.7, 0.)]))
    ])

    group1 = Group("Sample Instrument + Effects", [t1, t1_fx])

    section1 = Section("A Section", [group1], [(0, 100), (10, 80)], 4.0)

    song1 = Song("Test Song", "Com Poser", [section1])
    song1.emit()
