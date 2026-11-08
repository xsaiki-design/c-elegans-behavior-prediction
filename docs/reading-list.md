# Reading list — in the order that builds understanding

Each step says what to take away. You don't need to read papers cover to cover: Summary, the figures, and the
Discussion's first page usually carry it. Times are rough.

## 1. The animal and its circuit (≈ 2 h)

- **WormAtlas** — look up AVA, AVB, AIB, RIM, RIB. Take away: which neurons push backward vs forward.
  <https://www.wormatlas.org>
- **Gray, Hill & Bargmann 2005**, *PNAS* — "A circuit for navigation in *C. elegans*". Take away: reversals and turns
  are how the worm steers; which neurons control them. [doi](https://doi.org/10.1073/pnas.0409009101)

## 2. What the signal is (≈ 1.5 h)

- **Grienberger & Konnerth 2012**, *Neuron* — "Imaging calcium in neurons". Take away: fluorescence follows calcium,
  calcium follows electrical activity, with a delay and smoothing. [doi](https://doi.org/10.1016/j.neuron.2012.02.011)
- **Chen et al. 2013**, *Nature* — GCaMP6. Skim Figure 1 only. [doi](https://doi.org/10.1038/nature12354)
- **Yemini et al. 2021**, *Cell* — NeuroPAL. Take away: how every neuron gets a name. [doi](https://doi.org/10.1016/j.cell.2020.12.012)

## 3. Whole-brain imaging in worms (≈ 3 h)

- **Kato et al. 2015**, *Cell* — "Global brain dynamics embed the motor command sequence". Take away: brain activity
  cycles through forward → reverse → turn; most neurons join in. [doi](https://doi.org/10.1016/j.cell.2015.09.034)
- **Atanas & Kim et al. 2023**, *Cell* — **our dataset**. Take away: setup, what's recorded, how traces were processed,
  and their finding that neurons encode behaviour over different timescales. [doi](https://doi.org/10.1016/j.cell.2023.07.035)
- **Gordus et al. 2015**, *Cell* — why the same input doesn't always cause a reversal. Take away: the decision depends
  on network state, which is exactly what our model tries to read. [doi](https://doi.org/10.1016/j.cell.2015.02.018)
- **Hallinen et al. 2021**, *eLife* — decoding locomotion in moving worms. Closest prior work; know how ours differs
  (prediction ahead of time, tested on unseen worms). [doi](https://doi.org/10.7554/eLife.66135)

## 4. Analysis methods (≈ 4 h, spread out)

- ***An Introduction to Statistical Learning*** (free) — Ch. 4 logistic regression, Ch. 5 cross-validation,
  Ch. 6 regularisation, Ch. 12 PCA. <https://www.statlearning.com>
- **Cunningham & Yu 2014**, *Nat. Neurosci.* — dimensionality reduction for neural recordings. [doi](https://doi.org/10.1038/nn.3776)
- **Glaser et al. 2020**, *eNeuro* — machine learning for neural decoding, a practical guide. [doi](https://doi.org/10.1523/ENEURO.0506-19.2020)
- **Roberts et al. 2017**, *Ecography* — cross-validation with grouped and time-series data. [doi](https://doi.org/10.1111/ecog.02881)
- **Kaufman et al. 2012** — leakage in data mining. [doi](https://doi.org/10.1145/2382577.2382579)
- **Varoquaux 2018**, *NeuroImage* — small samples, big error bars. [doi](https://doi.org/10.1016/j.neuroimage.2017.06.061)
- **Saito & Rehmsmeier 2015**, *PLOS ONE* — precision-recall vs ROC. [doi](https://doi.org/10.1371/journal.pone.0118432)
- **scikit-learn cross-validation guide** — the grouped-data section. <https://scikit-learn.org/stable/modules/cross_validation.html>

## 5. Doing it reproducibly (≈ 1 h)

- **Wilson et al. 2017**, *PLOS Comp. Biol.* — "Good enough practices in scientific computing".
  [doi](https://doi.org/10.1371/journal.pcbi.1005510)
- **Sandve et al. 2013**, *PLOS Comp. Biol.* — "Ten simple rules for reproducible computational research".
  [doi](https://doi.org/10.1371/journal.pcbi.1003285)

All links were checked to resolve on 2026-11-08. Some journals need a subscription; most of these papers also have a
free copy on PubMed Central or the authors' sites.
