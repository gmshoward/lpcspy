\version "2.18.2"
\include "event-listener.ly"

<<
  \new Staff = "Bass" \with {
    instrumentName = #"Bass"
  }
  {
    \relative c, {
      \clef "bass"
      \time 3/4
      \tempo "Andante" 4 = 120
      c2([ e8 c'-.])
      g'2.
      f4-- e d-.
      c4-- c,-> r
    }
  }

  \new Staff = "Chords" \with {
    instrumentName = #"Chords"
  }
  {
    \oneVoice {
      \relative c' {
	\clef "treble"
	\time 3/4
	<< c2. e g >>
	<< g d b >>
	<< c f a >>
	<< g2 e c >>
	r4
      }
    }
  }
>>
