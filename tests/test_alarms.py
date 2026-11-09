from worms.alarms import caught


def test_a_reversal_counts_as_warned_only_if_the_alarm_came_early_enough():
    #        frame:  0    1    2    3    4    5    6     7    8
    risk = [0.1, 0.1, 0.9, 0.1, 0.1, 0.1, None, None, 0.1]
    reversals = [[6, 8]]  # starts at frame 6

    # alarm at frame 2 is 4 frames ahead: counts if 4 frames of warning is enough, not if 5 are required
    assert caught(risk, reversals, threshold=0.5, min_lead=4, horizon=8) == (1, 1)
    assert caught(risk, reversals, threshold=0.5, min_lead=5, horizon=8) == (0, 1)


def test_reversals_with_nothing_to_predict_from_are_not_counted():
    risk = [None, None, None, 0.1]
    assert caught(risk, [[2, 3]], threshold=0.5, min_lead=1, horizon=8) == (0, 0)
