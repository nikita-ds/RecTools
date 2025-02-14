#  Copyright 2024 MTS (Mobile Telesystems)
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Popularity metrics."""

import typing as tp

import pandas as pd

from rectools import Columns
from rectools.metrics.base import MetricAtK
from rectools.utils import select_by_type


class AvgRecPopularity(MetricAtK):
    r"""
    Average Recommendations Popularity metric.

    Calculate the average popularity of the recommended items in each list,
    where "popularity" of an item is the number of previous interactions
    with this item.

    .. math::
        ARP@k = \frac{1}{\left|U_{t}\right|}\sum_{u\in U_{t}^{}}\frac{\sum_{i\in L_{u}}\phi (i)}{\left| L_{u} \right |}

    where
    :math:`\phi (i)` is the number of previous interactions with item i.
    :math:`|U_{t}|` is the number of users in the test set.
    :math:`L_{u}` is the list of top k recommended items for user u.

    Parameters
    ----------
    k : int
        Number of items at the top of recommendations list that will be used to calculate metric.

    Examples
    --------
    >>> reco = pd.DataFrame(
    ...     {
    ...         Columns.User: [1, 1, 2, 2, 2, 3, 3],
    ...         Columns.Item: [1, 2, 3, 1, 2, 3, 2],
    ...         Columns.Rank: [1, 2, 1, 2, 3, 1, 2],
    ...     }
    ... )
    >>> prev_interactions = pd.DataFrame(
    ...     {
    ...         Columns.User: [1, 1, 2, 2, 3, 3],
    ...         Columns.Item: [1, 2, 1, 3, 1, 2],
    ...     }
    ... )
    >>> AvgRecPopularity(k=1).calc_per_user(reco, prev_interactions).values
    array([3., 1., 1.])
    >>> AvgRecPopularity(k=3).calc_per_user(reco, prev_interactions).values
    array([2.5, 2. , 1.5])
    """

    def calc(self, reco: pd.DataFrame, prev_interactions: pd.DataFrame) -> float:
        """
        Calculate metric value.

        Parameters
        ----------
        reco : pd.DataFrame
            Recommendations table with columns `Columns.User`, `Columns.Item`, `Columns.Rank`.
        prev_interactions : pd.DataFrame
            Table with previous user-item interactions,
            with columns `Columns.User`, `Columns.Item`.

        Returns
        -------
        float
            Value of metric (average between users).
        """
        per_user = self.calc_per_user(reco, prev_interactions)
        return per_user.mean()

    def calc_per_user(
        self,
        reco: pd.DataFrame,
        prev_interactions: pd.DataFrame,
    ) -> pd.Series:
        """
        Calculate metric values for all users.

        Parameters
        ----------
        reco : pd.DataFrame
            Recommendations table with columns `Columns.User`, `Columns.Item`, `Columns.Rank`.
        prev_interactions : pd.DataFrame
            Table with previous user-item interactions,
            with columns `Columns.User`, `Columns.Item`.

        Returns
        -------
        pd.Series
            Values of metric (index - user id, values - metric value for every user).
        """
        item_popularity = prev_interactions[Columns.Item].value_counts()
        item_popularity.name = "popularity"

        reco_k = reco.query(f"{Columns.Rank} <= @self.k")
        reco_prepared = reco_k.join(item_popularity, on=Columns.Item, how="left")
        reco_prepared["popularity"] = reco_prepared["popularity"].fillna(0)

        arp = reco_prepared.groupby(Columns.User)["popularity"].mean()
        return arp


PopularityMetric = AvgRecPopularity


def calc_popularity_metrics(
    metrics: tp.Dict[str, PopularityMetric],
    reco: pd.DataFrame,
    prev_interactions: pd.DataFrame,
) -> tp.Dict[str, float]:
    """
    Calculate popularity metrics (only AvgRP now).

    Warning: It is not recommended to use this function directly.
    Use `calc_metrics` instead.

    Parameters
    ----------
    metrics : dict(str -> PopularityMetric)
        Dict of metric objects to calculate,
        where key is metric name and value is metric object.
    reco : pd.DataFrame
        Recommendations table with columns `Columns.User`, `Columns.Item`, `Columns.Rank`.
    prev_interactions : pd.DataFrame
        Table with previous user-item interactions,
        with columns `Columns.User`, `Columns.Item`.

    Returns
    -------
    dict(str->float)
        Dictionary where keys are the same as keys in `metrics`
        and values are metric calculation results.
    """
    results = {}

    # ARP
    pop_metrics: tp.Dict[str, AvgRecPopularity] = select_by_type(metrics, AvgRecPopularity)
    for name, metric in pop_metrics.items():
        results[name] = metric.calc(reco, prev_interactions)

    return results
