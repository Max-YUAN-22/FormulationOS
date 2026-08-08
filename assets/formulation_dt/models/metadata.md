# Formulation DT Assets

This directory contains runtime assets for the Formulation DT module.
These files are **not tracked by git** and must be placed manually.

## Required Files

### `models/` directory

12 sklearn RandomForest models in Python 2 pickle format (`encoding="latin1"`):

| File                | Description                           |
| ------------------- | ------------------------------------- |
| `model_o1.pickle`   | Oral route level-1 classifier         |
| `model_o2a.pickle`  | Oral route level-2a classifier        |
| `model_o2bs.pickle` | Oral route level-2bs classifier       |
| `model_o2bn.pickle` | Oral route level-2bn classifier       |
| `model_o2bl.pickle` | Oral route level-2bl classifier       |
| `model_o2bc.pickle` | Oral route level-2bc classifier       |
| `model_i1.pickle`   | Injectable route level-1 classifier   |
| `model_i2a.pickle`  | Injectable route level-2a classifier  |
| `model_i2bo.pickle` | Injectable route level-2bo classifier |
| `model_i2bs.pickle` | Injectable route level-2bs classifier |
| `model_i2bl.pickle` | Injectable route level-2bl classifier |
| `model_i2bc.pickle` | Injectable route level-2bc classifier |

> These models were trained with scikit-learn 1.2.2. runner-dt uses `scikit-learn==1.2.2`
> and a `sys.modules` shim to load legacy pickle files.
