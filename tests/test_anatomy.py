from worms.anatomy import class_edges


def test_synapses_are_summed_between_neuron_classes_both_directions():
    chemical = {("AVAL", "AIBR"): 2, ("AIBL", "AVAR"): 3, ("AVAL", "AVAR"): 9, ("AVAL", "XYZ"): 5}
    electrical = {("AVAL", "AIBL"): 1, ("AIBL", "AVAL"): 1}  # symmetric table lists each junction both ways
    cls = {"AVAL": "AVA", "AVAR": "AVA", "AIBL": "AIB", "AIBR": "AIB"}  # XYZ isn't one of ours

    edges = class_edges(chemical, electrical, cls)

    # AVA<->AIB: chemical 2 + 3 (both directions), electrical 1 (counted once); within-class AVA->AVA dropped
    assert edges == [{"a": "AIB", "b": "AVA", "chemical": 5, "electrical": 1}]


from worms.anatomy import neuron_links, roles


def test_neuron_links_sum_both_directions_and_count_gap_junctions_once():
    chemical = {("AVAL", "AIBR"): 2, ("AIBR", "AVAL"): 1, ("AVAL", "XYZ"): 5}
    electrical = {("AVAL", "AVAR"): 3, ("AVAR", "AVAL"): 3}
    assert neuron_links(chemical, electrical, {"AVAL", "AVAR", "AIBR"}) == [["AIBR", "AVAL", 3], ["AVAL", "AVAR", 3]]


def test_roles_are_read_from_the_toolbox_text_without_running_it():
    text = 'A = [\n    "AVAL",\n    "AVAR",\n]\n\nfor cell in A:\n    cell_notes[cell] = "layer 1 interneuron"\n' \
           'for cell in B:\n    if cell in ["URXL", "URXR"]:\n        cell_notes[cell] = "O2, CO2, social signals, touch"\n'
    assert roles(text) == {"AVAL": "layer 1 interneuron", "AVAR": "layer 1 interneuron",
                           "URXL": "O2, CO2, social signals, touch", "URXR": "O2, CO2, social signals, touch"}
