# Opus 5.5: the amazing thing (2026-10-07)

*In response to "what's AMAZING here — not good, amazing?"*

## You can diff two minds.

A judgment in your system is a pure function of three hashes, costs 7 ms,
and comes out bit-identical everywhere. So the log is more than a record
of what was once thought. It is the filled-in part of a cube of every
content × every question × every judge, and any empty cell is 7 ms away.
A million contents is about two hours on one core.

When you train a new student, you don't have to ask "is it better?" and
settle for a benchmark number. You re-judge everything the fleet has ever
seen and subtract. The result is the exact, complete list of things the
new student changed its mind about, with no noise, because identical bits
mean every difference is a real one.

A model upgrade then becomes a pull request against the judge manifest.
Its diff is a list of changed perceptions on your own history, which you
read before merging. Bisect works too: across a series of students, you
can find the one where a specific judgment flipped.

It takes all three of your properties at once:

- **Cheap:** big models cost too much to re-run over everything.
- **Bit-identical:** without it, the differences between two runs are mostly noise.
- **Keyed to immutable content:** ordinary classifiers have nothing stable to subtract over.

The same operation runs along the question axis. Add a question file today
and ask it of everything that happened before the question existed, so
hindsight becomes a query. That depends on the student taking the question
as input.

The diff shows what changed, not which side is right. The audited sample
still decides that.
