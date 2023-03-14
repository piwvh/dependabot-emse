# [reaper](../reaper)

## Scripts

* [train.py](train.py)
  * The script was used to train two classification models:
    * Random forest tree based on the following six features: 'continuous_integration', 'community', 'documentation', 'history', 'license', 'unit_test'. Referred in the paper as the *modified model*;
    * Random forest tree based on the following eight features: 'architecture', 'continuous_integration', 'community', 'documentation', 'history', 'license', 'management', 'unit_test'. Referred in the paper as the *baseline model*;
  * The training is performed on the [*utility dataset*](data/utility.csv) [[1]](#1).
  * <strong>usage</strong>: ```python train.py```
  * <strong>output</strong>: [model/model_subset.pkl, model/model_full.pkl](model)
 
* [validate.py](validate.py)
  * The script was used to validate the two classification models using the [*validation dataset*](data/validation.csv) [[1]](#1).
  * <strong>usage</strong>: ```python validate.py```
  * <strong>output</strong>: [data/performance.csv](data/performance.csv)
  
* [classify.py](classify.py)
  * The script was used to perform classification (engineered vs non-engineered) for the [selected repositories](data/projects.csv) using the [*modified model*](model/model_subset.pkl).
  * <strong>usage</strong>: ```python classify.py```
  * <strong>output</strong>: [data/class.csv](data/class.csv), [../data/repositories/engineered.csv](../data/repositories/engineered.csv)
  
## Data

* [data/utility.csv](data/utility.csv)
  * The *utility dataset* constructed by Munaiah *et al.* [[1]](#1).

* [data/organization.csv](data/organization.csv)
  * The *organization dataset* constructed by Munaiah *et al.* [[1]](#1).

* [data/validation.csv](data/validation.csv)
  * The *validation dataset* constructed by Munaiah *et al.* [[1]](#1).
  
* [model/model_full.pkl](model/model_full.pkl)
  * The *baseline model* stored as a *pickle* file.
  
* [model/model_subset.pkl](model/model_subset.pkl)
  * The *modified model* stored as a *pickle* file.
  
* [data/performance.csv](data/performance.csv)
  * The file storing the results of the validation procedure for the two classification models.

* [data/projects.csv](data/projects.csv)
  * The file storing the list of the projects to compute the features for using the [modified implementation](https://github.com/andreiagaronian/reaper) of the [*Reaper*](https://github.com/RepoReapers/reaper) tool [[1]](#1).
  * The copy of [../data/repositories/repos_with_manifests.csv](../data/repositories/repos_with_manifests.csv).

* [data/results.csv](data/results.csv)
  * The file storing the feature values computed for the [selected projects](data/projects.csv) using the [modified implementation](https://github.com/andreiagaronian/reaper) of the [*Reaper*](https://github.com/RepoReapers/reaper) tool [[1]](#1).

* [data/class.csv](data/class.csv)
  * The file storing the results of the classification (engineered vs non-engineered) for the [selected repositories](data/projects.csv).



## References
<a id="1">[1]</a>
Munaiah, N., Kroh, S., Cabrey, C., & Nagappan, M. (2017). Curating github for engineered software projects. Empirical Software Engineering, 22(6), 3219-3253. [DOI 10.1007/s10664-017-9512-6](https://doi.org/10.1007/s10664-017-9512-6).