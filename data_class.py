from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RaceBasicData(object):
    race_group_name: str
    race_name: str
    grade: str
    race_num: str
    start_datetime: str
    place: str
    distance: int
    orbit: int


@dataclass
class Player(object):
    name: str
    come_from: str
    age: int
    period: int
    rank: str
    frame_num: int
    car_num: int
    competitive_score: float
    leg_quality: str
    s: int
    b: int
    nige: int
    makuri: int
    sashi: int
    mark: int
    first: int
    second: int
    third: int
    outside: int
    win_rate: float
    double_rate: float
    triple_rate: float
    gear_multiple: float
    first_flg: str
    second_flg: str
    first_second_flg: str


@dataclass
class DataAnalysisOne(object):
    name: str
    first: int
    second: int
    third: int
    outside: int
    num_of_runs: int
    win_rate: int
    double_rate: int
    triple_rate: int


@dataclass
class DataAnalysis(object):
    data_analysis_ones: list[DataAnalysisOne]


@dataclass
class Result(object):
    race_name: str
    order_of_arrival: str


@dataclass
class RecentResultOne(object):
    grade: str
    place: str
    results: list[Result]


@dataclass
class RecentResult(object):
    section1: Result
    section2: Result
    recent_result_ones: list[RecentResultOne]


@dataclass
class MatchResult(object):
    win_num: int
    lose_num: int
