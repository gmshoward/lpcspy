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
      \tempo "Andante" 4 = 100
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
    %\oneVoice {
    %  \relative c' {
    %    \clef "treble"
    %    \time 3/4
    %    << c2. e g >>
    %    << g d b >>
    %    << c f a >>
    %    << g2 e c >>
    %    r4
    %  }
    %}
    \relative c' {
        << { c2. }  \\ { e2  d4~ } \\ { g2.~ } >> |
        << { b,2. } \\ { d2. }     \\ { g2  a4~ } >> |
        << { c,2. } \\ { f2. }     \\ { a2. } >> |
        <    c,          e              g      >2. |
    }
  }
>>
