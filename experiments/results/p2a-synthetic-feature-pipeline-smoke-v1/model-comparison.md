# P2-A synthetic pipeline smoke: model comparison

All values below are from a deterministic, repository-owned synthetic feature fixture. They validate only experiment plumbing; they are not measurements of AI-image detection, generator attribution, or real-world robustness.

| Baseline | Accuracy | F1 | AUROC | PR-AUC | ECE | Brier score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| logistic_regression | 0.875000 | 0.857143 | 0.930556 | 0.948902 | 0.119634 | 0.099214 |
| linear_layer | 0.875000 | 0.857143 | 0.937500 | 0.954778 | 0.166789 | 0.099912 |
| tiny_mlp | 0.750000 | 0.727273 | 0.652778 | 0.768015 | 0.251492 | 0.227202 |

Do not select a production model from this table. P2-B requires approved image data, frozen splits, real transformations, and review of failure modes.
