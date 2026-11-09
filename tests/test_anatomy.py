from worms.anatomy import class_edges


def test_synapses_are_summed_between_neuron_classes_both_directions():
    chemical = {("AVAL", "AIBR"): 2, ("AIBL", "AVAR"): 3, ("AVAL", "AVAR"): 9, ("AVAL", "XYZ"): 5}
    electrical = {("AVAL", "AIBL"): 1, ("AIBL", "AVAL"): 1}  # symmetric table lists each junction both ways
    cls = {"AVAL": "AVA", "AVAR": "AVA", "AIBL": "AIB", "AIBR": "AIB"}  # XYZ isn't one of ours

    edges = class_edges(chemical, electrical, cls)

    # AVA<->AIB: chemical 2 + 3 (both directions), electrical 1 (counted once); within-class AVA->AVA dropped
    assert edges == [{"a": "AIB", "b": "AVA", "chemical": 5, "electrical": 1}]
