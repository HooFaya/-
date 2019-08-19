"""
Concrete query strategy classes.
"""
from __future__ import absolute_import

import os
ON_RTD = os.environ.get('READTHEDOCS', None) == 'True'
import logging
LOGGER = logging.getLogger(__name__)

from .active_learning_by_learning import ActiveLearningByLearning
from .uncertainty_sampling import UncertaintySampling
from .query_by_committee import QueryByCommittee
from .quire import QUIRE
from .random_sampling import RandomSampling
from .density_weighted_uncertainty_sampling import DWUS
from .uncertainty_sampling_test import UncertaintySampling_test
# don't import c extentions when on readthedocs server
from .density_weighted_meta import DensityWeightedMeta
if not ON_RTD:
    try:
        from ._variance_reduction import estVar
        from .variance_reduction import VarianceReduction
    except ModuleNotFoundError:
        LOGGER.warning("Variance Reduction C-extension not compiled. "
                       "Install package with environment variable "
                       "LIBACT_BUILD_VARIANCE_REDUCTION=1 if intend to run "
                       "VarianceReduction")
    try:
        from libact.query_strategies._hintsvm import hintsvm_query
        from .hintsvm import HintSVM
    except ModuleNotFoundError:
        LOGGER.warning("HintSVM C-extension not compiled. "
                       "Install package with environment variable"
                       "LIBACT_BUILD_HINTSVM=1 if intend to run HintSVM")
else:
    from .variance_reduction import VarianceReduction
    from .hintsvm import HintSVM

"""

集成了9种集成策略：
围绕着不确定性，差异性
不确定性：
差异性：这个比较好理解，采样得到包含信息量最大的样本，弊端：我们的采样模型只考虑单个样本，没有顾及到
代表性：
ActiveLearningByLearning:自适应算法，学到最合适的查询策略
DWUS:Density Weighted Uncertainty Sampling，基于kmeans的查询策略，但是内部分类器只能用LR
QUIRE

"""
__all__ = [
    'ActiveLearningByLearning',
    'DWUS',
    'HintSVM',
    'QUIRE',
    'QueryByCommittee',
    'RandomSampling',
    'UncertaintySampling',
    'VarianceReduction',
    'DensityWeightedMeta',
    "UncertaintySampling_test"
]
