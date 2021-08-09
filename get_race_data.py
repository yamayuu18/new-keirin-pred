from __future__ import annotations

import os
import platform
import re
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from time import sleep
from typing import TextIO

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm

import data_class

DRIVER_SITE: str = 'chromedriver.exe' if platform.system() == 'Windows' else '/Applications/chromedriver'
CURRENT_DIR: str = 'race_data'
ORIGINAL_URL: str = 'https://keirin.netkeiba.com/db/search_result/race.html?word=&start_year=none&start_mon=none&end_year=none&end_mon=none&jyo=&sort=1&submit='
FILENAME: str = 'race_data'
HEADER: str = (
    'レースグループ名,レース名,グレード,ラウンド,開催日時,開催場所,距離,周回,1着,2着,'
    '選手名,出身,年齢,期別,級班,枠番,車番,競走得点,脚質,S,B,逃げ,まくり,差し,マーク,1着,2着,3着,着外,勝率,2連対率,3連対率,ギヤ倍数,'
    '項目名_1,1着_1,2着_1,3着_1,着外_1,出走回数_1,勝率_1,2連対率_1,3連対率_1,'
    '項目名_2,1着_2,2着_2,3着_2,着外_2,出走回数_2,勝率_2,2連対率_2,3連対率_2,'
    '項目名_3,1着_3,2着_3,3着_3,着外_3,出走回数_3,勝率_3,2連対率_3,3連対率_3,'
    '項目名_4,1着_4,2着_4,3着_4,着外_4,出走回数_4,勝率_4,2連対率_4,3連対率_4,'
    '今節1_レース名,今節1_着順,今節2_レース名,今節2_着順,'
    '直近1_グレード,直近1_開催場所,直近1_レース名1,直近1_着順1,直近1_レース名2,直近1_着順2,直近1_レース名3,直近1_着順3,直近1_レース名4,直近1_着順4,直近1_レース名5,直近1_着順5,'
    '直近2_グレード,直近2_開催場所,直近2_レース名1,直近2_着順1,直近2_レース名2,直近2_着順2,直近2_レース名3,直近2_着順3,直近2_レース名4,直近2_着順4,直近2_レース名5,直近2_着順5,'
    '直近3_グレード,直近3_開催場所,直近3_レース名1,直近3_着順1,直近3_レース名2,直近3_着順2,直近3_レース名3,直近3_着順3,直近3_レース名4,直近3_着順4,直近3_レース名5,直近3_着順5,'
    '直近4_グレード,直近4_開催場所,直近4_レース名1,直近4_着順1,直近4_レース名2,直近4_着順2,直近4_レース名3,直近4_着順3,直近4_レース名4,直近4_着順4,直近4_レース名5,直近4_着順5,'
    '直近5_グレード,直近5_開催場所,直近5_レース名1,直近5_着順1,直近5_レース名2,直近5_着順2,直近5_レース名3,直近5_着順3,直近5_レース名4,直近5_着順4,直近5_レース名5,直近5_着順5,'
    '直近6_グレード,直近6_開催場所,直近6_レース名1,直近6_着順1,直近6_レース名2,直近6_着順2,直近6_レース名3,直近6_着順3,直近6_レース名4,直近6_着順4,直近6_レース名5,直近6_着順5,'
    '直近7_グレード,直近7_開催場所,直近7_レース名1,直近7_着順1,直近7_レース名2,直近7_着順2,直近7_レース名3,直近7_着順3,直近7_レース名4,直近7_着順4,直近7_レース名5,直近7_着順5,'
    '直近8_グレード,直近8_開催場所,直近8_レース名1,直近8_着順1,直近8_レース名2,直近8_着順2,直近8_レース名3,直近8_着順3,直近8_レース名4,直近8_着順4,直近8_レース名5,直近8_着順5,'
    '直近9_グレード,直近9_開催場所,直近9_レース名1,直近9_着順1,直近9_レース名2,直近9_着順2,直近9_レース名3,直近9_着順3,直近9_レース名4,直近9_着順4,直近9_レース名5,直近9_着順5,'
    '直近10_グレード,直近10_開催場所,直近10_レース名1,直近10_着順1,直近10_レース名2,直近10_着順2,直近10_レース名3,直近10_着順3,直近10_レース名4,直近10_着順4,直近10_レース名5,直近10_着順5,'
    '直近11_グレード,直近11_開催場所,直近11_レース名1,直近11_着順1,直近11_レース名2,直近11_着順2,直近11_レース名3,直近11_着順3,直近11_レース名4,直近11_着順4,直近11_レース名5,直近11_着順5,'
    '直近12_グレード,直近12_開催場所,直近12_レース名1,直近12_着順1,直近12_レース名2,直近12_着順2,直近12_レース名3,直近12_着順3,直近12_レース名4,直近12_着順4,直近12_レース名5,直近12_着順5,'
    '直近13_グレード,直近13_開催場所,直近13_レース名1,直近13_着順1,直近13_レース名2,直近13_着順2,直近13_レース名3,直近13_着順3,直近13_レース名4,直近13_着順4,直近13_レース名5,直近13_着順5,'
    '直近14_グレード,直近14_開催場所,直近14_レース名1,直近14_着順1,直近14_レース名2,直近14_着順2,直近14_レース名3,直近14_着順3,直近14_レース名4,直近14_着順4,直近14_レース名5,直近14_着順5,'
    '直近15_グレード,直近15_開催場所,直近15_レース名1,直近15_着順1,直近15_レース名2,直近15_着順2,直近15_レース名3,直近15_着順3,直近15_レース名4,直近15_着順4,直近15_レース名5,直近15_着順5,'
    '直近16_グレード,直近16_開催場所,直近16_レース名1,直近16_着順1,直近16_レース名2,直近16_着順2,直近16_レース名3,直近16_着順3,直近16_レース名4,直近16_着順4,直近16_レース名5,直近16_着順5,'
    '直近17_グレード,直近17_開催場所,直近17_レース名1,直近17_着順1,直近17_レース名2,直近17_着順2,直近17_レース名3,直近17_着順3,直近17_レース名4,直近17_着順4,直近17_レース名5,直近17_着順5,'
    '直近18_グレード,直近18_開催場所,直近18_レース名1,直近18_着順1,直近18_レース名2,直近18_着順2,直近18_レース名3,直近18_着順3,直近18_レース名4,直近18_着順4,直近18_レース名5,直近18_着順5,'
    '直近19_グレード,直近19_開催場所,直近19_レース名1,直近19_着順1,直近19_レース名2,直近19_着順2,直近19_レース名3,直近19_着順3,直近19_レース名4,直近19_着順4,直近19_レース名5,直近19_着順5,'
    '直近20_グレード,直近20_開催場所,直近20_レース名1,直近20_着順1,直近20_レース名2,直近20_着順2,直近20_レース名3,直近20_着順3,直近20_レース名4,直近20_着順4,直近20_レース名5,直近20_着順5,'
    '直近21_グレード,直近21_開催場所,直近21_レース名1,直近21_着順1,直近21_レース名2,直近21_着順2,直近21_レース名3,直近21_着順3,直近21_レース名4,直近21_着順4,直近21_レース名5,直近21_着順5,'
    '直近22_グレード,直近22_開催場所,直近22_レース名1,直近22_着順1,直近22_レース名2,直近22_着順2,直近22_レース名3,直近22_着順3,直近22_レース名4,直近22_着順4,直近22_レース名5,直近22_着順5,'
    '直近23_グレード,直近23_開催場所,直近23_レース名1,直近23_着順1,直近23_レース名2,直近23_着順2,直近23_レース名3,直近23_着順3,直近23_レース名4,直近23_着順4,直近23_レース名5,直近23_着順5,'
    '直近24_グレード,直近24_開催場所,直近24_レース名1,直近24_着順1,直近24_レース名2,直近24_着順2,直近24_レース名3,直近24_着順3,直近24_レース名4,直近24_着順4,直近24_レース名5,直近24_着順5,'
    '直近25_グレード,直近25_開催場所,直近25_レース名1,直近25_着順1,直近25_レース名2,直近25_着順2,直近25_レース名3,直近25_着順3,直近25_レース名4,直近25_着順4,直近25_レース名5,直近25_着順5,'
    '直近26_グレード,直近26_開催場所,直近26_レース名1,直近26_着順1,直近26_レース名2,直近26_着順2,直近26_レース名3,直近26_着順3,直近26_レース名4,直近26_着順4,直近26_レース名5,直近26_着順5,'
    '直近27_グレード,直近27_開催場所,直近27_レース名1,直近27_着順1,直近27_レース名2,直近27_着順2,直近27_レース名3,直近27_着順3,直近27_レース名4,直近27_着順4,直近27_レース名5,直近27_着順5,'
    '直近28_グレード,直近28_開催場所,直近28_レース名1,直近28_着順1,直近28_レース名2,直近28_着順2,直近28_レース名3,直近28_着順3,直近28_レース名4,直近28_着順4,直近28_レース名5,直近28_着順5,'
    '直近29_グレード,直近29_開催場所,直近29_レース名1,直近29_着順1,直近29_レース名2,直近29_着順2,直近29_レース名3,直近29_着順3,直近29_レース名4,直近29_着順4,直近29_レース名5,直近29_着順5,'
    '直近30_グレード,直近30_開催場所,直近30_レース名1,直近30_着順1,直近30_レース名2,直近30_着順2,直近30_レース名3,直近30_着順3,直近30_レース名4,直近30_着順4,直近30_レース名5,直近30_着順5,'
    '対戦勝ち数,対戦負け数\n'
)


def end_page_correction(driver: webdriver.Chrome, end_page_num: int) -> int:
    """
    指定された終了ページ数が実ページ数を超えないように設定する

    Parameters
    ----------
    driver : webdriver.Chrome
        Webドライバー(chrome)
    end_page_num : int
        指定された終了ページ数

    Returns
    -------
    int
        実ページ数を超えないように設定された終了ページ数
    """

    # 全ページ数の取得
    driver.find_element_by_link_text('最後').click()
    sleep(1)
    total_page_num: int = int(driver.find_element_by_xpath('//a[@class="Page_Active"]').text)
    driver.get(ORIGINAL_URL)
    sleep(1)

    # Webスクレイピング終了ページの補正
    if end_page_num > total_page_num:
        end_page_num = total_page_num

    return end_page_num


def start_page_transition(driver: webdriver.Chrome, start_page_num: int) -> None:
    """
    指定された開始ページ数までページ遷移する

    Parameters
    ----------
    driver : webdriver.Chrome
        Webドライバー(chrome)
    start_page_num : int
        指定された開始ページ数
    """

    if start_page_num > 1:
        for _ in range(1, start_page_num):
            driver.find_element_by_link_text('次へ').click()
            sleep(1)


def get_date_and_venue(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """
    開催日と開催場所を取得する

    Parameters
    ----------
    soup : BeautifulSoup
        BeautifulSoupオブジェクト

    Returns
    -------
    list[tuple[str, str]]
        開催日と開催場所をタプル形式にして、リストに追加
    """
    date_and_venue: list[tuple[str, str]] = []

    # 開催日と開催場所の取得
    for data in soup.select('.DataBox_01'):
        (date, venue) = data.p.get_text(strip=True).split()
        date_and_venue.append((date, venue))

    return date_and_venue


def date_split(date_str: str) -> list[datetime]:
    """
    期間のある日付を分割して、1日単位で日付リストに設定する

    Parameters
    ----------
    date_str : str
        期間のある日付文字列

    Returns
    -------
    list[datetime]
        1日単位での日付リスト
    """
    dates: list[datetime] = []

    date_split: list[str] = date_str.split('～')
    tdate: datetime = datetime.strptime(date_split[0], '%Y/%m/%d')
    dates.append(tdate)
    tdate_end = datetime.strptime(date_split[1], '%Y/%m/%d')

    while(tdate<tdate_end):
        tdate += timedelta(days=1)
        dates.append(tdate)
    
    return dates


def get_umatan(soup: BeautifulSoup) -> tuple[int, int]:
    """
    期間のある日付を分割して、1日単位で日付リストに設定する

    Parameters
    ----------
    soup : BeautifulSoup
        BeautifulSoupオブジェクト

    Returns
    -------
    tuple[int, int]
        1着・2着順のタプル
    """
    # 2車単の取得
    temp_rank = soup.select_one('.Umatan').td.get_text(strip=True).split('>')
    return (int(temp_rank[0]), int(temp_rank[1]))


def get_race_basic_data(soup: BeautifulSoup, date: datetime, venue: str) -> data_class.RaceBasicData:
    """
    レース基本データを取得し、RaceBasicDataのインスタンスを返却する

    Parameters
    ----------
    soup : BeautifulSoup
        BeautifulSoupオブジェクト

    date : datetime
        開催日

    venue : str
        開催場所

    Returns
    -------
    data_class.RaceBasicData
        RaceBasicDataクラスのインスタンス
    """
    race_data_list: list[str] = soup.select_one('.Race_Data').get_text(strip=True).split()
    hour_and_minute: list[str] = race_data_list[1].split(':')
    tdate = date.replace(hour=int(hour_and_minute[0]), minute=int(hour_and_minute[1]))

    race_basic_data = data_class.RaceBasicData(
        soup.select_one('.Race_GroupName').get_text(strip=True),
        soup.select_one('.Race_Name').get_text(strip=True),
        soup.select_one('.Icon_GradeType').get_text(strip=True),
        soup.select_one('.Race_Num').get_text(strip=True),
        tdate.strftime('%Y-%m-%d %H:%M'),
        venue,
        int(race_data_list[4].rstrip('m')),
        int(race_data_list[5].rstrip('周'))
    )

    return race_basic_data


def get_player_data(soup: BeautifulSoup) -> list[data_class.Player]:
    """
    レース基本データを取得し、Playerクラスのインスタンスのリストを返却する

    Parameters
    ----------
    soup : BeautifulSoup
        BeautifulSoupオブジェクト

    Returns
    -------
    list[data_class.Player]
        レースに参加する選手のPlayerクラスのインスタンスをリスト化する
    """
    player_data_list: list[data_class.Player] = []
    player_list = soup.select_one('.RaceCard_Simple_Table_Static').select('.PlayerList')

    for player in player_list:
        # 出身・年齢の取得
        come_from_age = player.select_one('.Player_InfoWrap.DispA').select_one('.PlayerFrom').get_text(strip=True).split()
        # 期別・級班の取得
        period_rank = player.select_one('.Player_InfoWrap.DispA').dl.select_one('.PlayerClass').get_text(strip=True).split()
        # 各種データの取得
        data_list = player.select('.RaceCardCell01')

        gear_multiple = data_list[18].get_text(strip=True)
        if '↓' in gear_multiple:
            gear_multiple = re.sub('^.+↓', '', gear_multiple)

        player_data_list.append(
            data_class.Player(
                player.select_one('.Player_InfoWrap.DispA').select_one('.Player01').get_text(strip=True),
                come_from_age[0],
                int(come_from_age[1].rstrip('歳')),
                period_rank[0],
                period_rank[1],
                int(data_list[0].get_text(strip=True)),
                int(data_list[1].get_text(strip=True)),
                float(data_list[3].get_text(strip=True)),
                data_list[4].get_text(strip=True)[1:],
                int(data_list[5].get_text(strip=True)),
                int(data_list[6].get_text(strip=True)),
                int(data_list[7].get_text(strip=True)),
                int(data_list[8].get_text(strip=True)),
                int(data_list[9].get_text(strip=True)),
                int(data_list[10].get_text(strip=True)),
                int(data_list[11].get_text(strip=True)),
                int(data_list[12].get_text(strip=True)),
                int(data_list[13].get_text(strip=True)),
                int(data_list[14].get_text(strip=True)),
                float(data_list[15].get_text(strip=True).rstrip('%')),
                float(data_list[16].get_text(strip=True).rstrip('%')),
                float(data_list[17].get_text(strip=True).rstrip('%')),
                float(gear_multiple)
            )
        )

    return player_data_list


def get_data_analysis(soup: BeautifulSoup) -> list[data_class.DataAnalysis]:
    """
    データ分析データを取得し、DataAnalysisクラスのインスタンスのリストを返却する

    Parameters
    ----------
    soup : BeautifulSoup
        BeautifulSoupオブジェクト

    Returns
    -------
    list[data_class.DataAnalysis]
        レースに参加する選手のDataAnalysisクラスのインスタンスをリスト化する
    """
    datas = soup.select_one('.Data01_Table.Default tbody').select('tr')

    data_analysis_list: list[data_class.DataAnalysis] = []
    data_analysis_one_list: list[data_class.DataAnalysisOne] = []

    for i, data in enumerate(datas):
        if 1 <= i % 5 <= 4:
            name: str = ''
            num_list: list[int] = []        
            rate_list: list[float] = []
            for td in data.select('td'):
                try:
                    if '%' in td.get_text():
                        rate_list.append(float(td.get_text(strip=True).rstrip('%')))
                    else:
                        num_list.append(int(td.get_text(strip=True)))
                except ValueError:
                    name = td.get_text(strip=True)

            data_analysis_one_list.append(
                data_class.DataAnalysisOne(
                    name,
                    *num_list,
                    *rate_list
                )
            )

        else:
            if i > 0:
                data_analysis_list.append(
                    data_class.DataAnalysis(
                        data_analysis_one_list
                    )
                )
                data_analysis_one_list = []
    
    data_analysis_list.append(
        data_class.DataAnalysis(
            data_analysis_one_list
        )
    )

    return data_analysis_list


def get_recent_result(soup: BeautifulSoup) -> list[data_class.RecentResult]:
    """
    直近成績データを取得し、RecentResultクラスのインスタンスのリストを返却する

    Parameters
    ----------
    soup : BeautifulSoup
        BeautifulSoupオブジェクト

    Returns
    -------
    list[data_class.RecentResult]
        レースに参加する選手のRecentResultクラスのインスタンスをリスト化する
    """
    recent_result_list: list[data_class.RecentResult] = []
    
    player_data_list = soup.select('.RaceCard_Result_Table .PlayerList')

    for player_data in player_data_list:
        result_data_list = player_data.select('[class^="detail_table_tbody"]')

        recent_result_one_list: list[data_class.RecentResultOne] = []
        result_list: list[data_class.Result] = []
        section_count: int = 0
        section1: data_class.Result = data_class.Result('', '')
        section2: data_class.Result = data_class.Result('', '')
        exist_section: bool = True
        grade: str = ''
        place: str = ''

        for i, result in enumerate(result_data_list):
            if result.select_one('.Icon_GradeType'):
                if not exist_section:
                    if len(result_list) < 5:
                        for _ in range(5 - len(result_list)):
                            result_list.append(
                                data_class.Result(
                                    '',
                                    ''
                                )
                            )

                    recent_result_one_list.append(
                        data_class.RecentResultOne(
                            grade,
                            place,
                            result_list
                        )
                    )
                    result_list = []

                exist_section = False

                grade = result.select_one('.Icon_GradeType').get_text(strip=True)
                place = result.select_one('.JyoName').get_text(strip=True)

            elif result.select_one('.RaceName'):
                race_name = result.select_one('.RaceName').get_text(strip=True).replace('\u3000', '')
                order_of_arrival = result.select_one('.result_no').get_text(strip=True)

                result_list.append(
                    data_class.Result(
                        race_name,
                        order_of_arrival
                    )
                )

            elif result.get_text(strip=True) != '':
                race_order = result.a.get_text(strip=True).replace('\u3000', '')
                if section_count == 0 and exist_section:
                    section1 = data_class.Result(
                        race_order[:-1],
                        race_order[-1:]
                    )
                    section_count += 1
                elif section_count == 1 and exist_section:
                    section2 = data_class.Result(
                        race_order[:-1],
                        race_order[-1:]
                    )
                    section_count += 1

        if len(result_list) < 5:
            for _ in range(5 - len(result_list)):
                result_list.append(
                    data_class.Result(
                        '',
                        ''
                    )
                )

        recent_result_one_list.append(
            data_class.RecentResultOne(
                grade,
                place,
                result_list
            )
        )

        if len(recent_result_one_list) < 30:
            for _ in range(30 - len(recent_result_one_list)):
                result_list = []
                for _ in range(5):
                    result_list.append(
                        data_class.Result(
                            '',
                            ''
                        )
                    )

                recent_result_one_list.append(
                    data_class.RecentResultOne(
                        '',
                        '',
                        result_list
                    )
                )

        recent_result_list.append(
            data_class.RecentResult(
                section1,
                section2,
                recent_result_one_list
            )
        )

    return recent_result_list


def get_match_result(soup: BeautifulSoup, player_num: int) -> list[data_class.MatchResult]:
    """
    対戦表データを取得し、MatchResultクラスのインスタンスのリストを返却する

    Parameters
    ----------
    soup : BeautifulSoup
        BeautifulSoupオブジェクト

    player_num : int
        出場選手数

    Returns
    -------
    list[data_class.MatchResult]
        レースに参加する選手のMatchResultクラスのインスタンスをリスト化する
    """
    player_data_list = soup.select('.RaceCard_Simple_Table_Static .PlayerList')

    match_result_list: list[data_class.MatchResult] = []

    if len(player_data_list) > 0:
        for player_data in player_data_list:
            result = player_data.select_one('.Player_Info + td').get_text(strip=True)
            win_lose = result.split('-')
            match_result_list.append(
                data_class.MatchResult(
                    int(win_lose[0]),
                    int(win_lose[1])
                )
            ) 
    else:
        for _ in range(player_num):
            match_result_list.append(
                data_class.MatchResult(
                    0,
                    0
                )
            ) 

    return match_result_list


def transform_data_analysis_csv(data_analysis_list: list[data_class.DataAnalysis]) -> list[str]:
    """
    対戦表データを取得し、MatchResultクラスのインスタンスのリストを返却する

    Parameters
    ----------
    data_analysis_list : list[data_class.DataAnalysis]
        レースに参加する選手のDataAnalysisクラスのインスタンスのリスト

    Returns
    -------
    list[str]
        レースに参加する選手のDataAnalysisクラスのインスタンスをcsv形式に変換
    """
    data_analysis_csv_list: list[str] = []

    for d_1 in data_analysis_list:
        data_csv: str = ''
        is_first_set: bool = True
        for d_2 in d_1.data_analysis_ones:
            for d_3 in asdict(d_2).values():
                if is_first_set:
                    data_csv = str(d_3)
                    is_first_set = False
                else:
                    data_csv += ',' + str(d_3)
        data_analysis_csv_list.append(data_csv)

    return data_analysis_csv_list    



def transform_recent_result_csv(recent_result_list: list[data_class.RecentResult]) -> list[str]:
    """
    対戦表データを取得し、MatchResultクラスのインスタンスのリストを返却する

    Parameters
    ----------
    recent_result_list : list[data_class.RecentResult]
        レースに参加する選手のRecentResultクラスのインスタンスのリスト

    Returns
    -------
    list[str]
        レースに参加する選手のRecentResultクラスのインスタンスをcsv形式に変換
    """
    recent_result_csv_list: list[str] = []

    for d_1 in recent_result_list:
        data_csv: str = d_1.section1.race_name
        data_csv += ',' + d_1.section1.order_of_arrival
        data_csv += ',' + d_1.section2.race_name
        data_csv += ',' + d_1.section2.order_of_arrival

        for d_2 in d_1.recent_result_ones:
            for d_3 in asdict(d_2).values():
                if isinstance(d_3, str):
                    data_csv += ',' + d_3
                else:
                    for d_3_1 in d_3:
                        for d_3_2 in d_3_1.values():
                            data_csv += ',' + d_3_2

        recent_result_csv_list.append(data_csv)

    return recent_result_csv_list


def date_and_race_page_scraping(driver,
                                date_and_venue: tuple[str, str],
                                race_data_file: TextIO) -> None:
    """
    レース一覧ページから情報を抽出し、レース出場選手結果ファイル、
    レース結果ファイルを出力する

    Parameters
    ----------
    driver : [type]
        Webドライバー(chrome)
    date_and_venue : tuple[str, str]
        日付と会場のタプル
    race_data_file : TextIO
        レースデータファイル
    """
    # レース一覧ページのURLの取得
    date_and_race_url: str = driver.current_url

    # 開催日リンクの取得
    date_list = driver.find_elements_by_xpath('//div[@class="Tab_RaceDaySelect p00"]/ul/li/a')

    # 日付の分割
    dates: list[datetime] = date_split(date_and_venue[0])

    # 開催日単位での処理
    for date_count in range(len(date_list)):

        # 開催日リンクの取得(古いセッション参照対応用)
        trans_date_list = driver.find_elements_by_xpath('//div[@class="Tab_RaceDaySelect p00"]/ul/li/a')

        # 開催日ページへの遷移
        trans_date_list[date_count].click()
        sleep(1)

        # 開催日単位レース詳細ページ要素の取得(古いセッション参照対応用)
        date_and_race_list = driver.find_elements_by_xpath('//div[@class="RaceList_SlideBoxItem"]')

        # 開催日単位レース詳細ページリンクの取得
        race_list = date_and_race_list[date_count].find_elements_by_tag_name('a')

        # レース詳細ページ単位での処理
        for race_num in range(len(race_list)):
            # 開催日単位レース詳細ページ要素の取得(古いセッション参照対応用)
            trans_date_and_race_list = driver.find_elements_by_xpath('//div[@class="RaceList_SlideBoxItem"]')

            # 開催日単位レース詳細ページリンクの取得(古いセッション参照対応用)
            trans_race_list = trans_date_and_race_list[date_count].find_elements_by_tag_name('a')

            # レース詳細ページへの遷移
            trans_race_list[race_num].click()
            sleep(1)
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # 1着・2着の取得
            if soup.select_one('.Umatan').td.get_text(strip=True) == '':
                # レース一覧ページへ戻る
                driver.get(date_and_race_url)
                sleep(1)
                # 開催日ページへの遷移
                trans_date_list = driver.find_elements_by_xpath('//div[@class="Tab_RaceDaySelect p00"]/ul/li/a')
                trans_date_list[date_count].click()
                sleep(1)
                continue
            else:
                ranking: tuple[int, int] = get_umatan(soup)

            # 出走表ページへの遷移
            driver.find_element_by_link_text('出走表').click()
            sleep(1)
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # レース基本データの取得
            race_basic_data: data_class.RaceBasicData = get_race_basic_data(soup,
                                                                            dates[date_count],
                                                                            date_and_venue[1])

            # 出場選手データの取得
            player_data_list: list[data_class.Player] = get_player_data(soup)

            # データ分析ページへの遷移
            driver.find_element_by_link_text('データ分析').click()
            sleep(1)
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # データ分析データの取得
            data_analysis_list: list[data_class.DataAnalysis] = get_data_analysis(soup)

            # 直近成績ページへの遷移
            driver.find_element_by_link_text('直近成績').click()
            sleep(1)
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # 直近成績データの取得
            recent_result_list: list[data_class.RecentResult] = get_recent_result(soup)

            # 対戦表ページへの遷移
            driver.find_element_by_link_text('対戦表').click()
            sleep(1)
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # 対戦表データの取得
            match_result_list: list[data_class.MatchResult] = get_match_result(soup,
                                                                               len(player_data_list))

            # データ分析データのcsv変換
            data_analysis_csv_list: list[str] = transform_data_analysis_csv(data_analysis_list)

            # 直近成績データのcsv変換
            recent_result_csv_list: list[str] = transform_recent_result_csv(recent_result_list)

            # ファイルへの書き込み
            for i, player_data in enumerate(player_data_list):
                race_data_file.write(
                    ','.join([str(d) for d in asdict(race_basic_data).values()]) +
                    ',' + str(ranking[0]) + ',' + str(ranking[1]) + 
                    ',' + ','.join([str(d) for d in asdict(player_data).values()]) + 
                    ',' + data_analysis_csv_list[i] +
                    ',' + recent_result_csv_list[i] +
                    ',' + ','.join([str(d) for d in asdict(match_result_list[i]).values()]) +  '\n'
                )

            # レース一覧ページへ戻る
            driver.get(date_and_race_url)
            sleep(1)
            # 開催日ページへの遷移
            trans_date_list = driver.find_elements_by_xpath('//div[@class="Tab_RaceDaySelect p00"]/ul/li/a')
            trans_date_list[date_count].click()
            sleep(1)


def main() -> None:
    try:
        # Seleniumの設定・操作
        options: Options = Options()
        options.add_argument('--headless')
        driver: webdriver.Chrome = webdriver.Chrome(DRIVER_SITE, options=options)
        # driver: webdriver.Chrome = webdriver.Chrome(DRIVER_SITE)
        driver.get(ORIGINAL_URL)
        sleep(1)

        # Webスクレイピング開始・終了ページの設定
        start_page_num: int = 7
        end_page_num: int = 8
        
        # Webスクレイピング終了ページの補正
        end_page_num = end_page_correction(driver, end_page_num)

        # Webスクレイピング開始ページへの遷移
        start_page_transition(driver, start_page_num)

        race_group_url: str = driver.current_url

        for page_num in tqdm(range(start_page_num, end_page_num + 1)):
            race_data_file: TextIO = open(os.path.join(CURRENT_DIR, FILENAME + str(page_num) + '.csv'), 'w')
            race_data_file.write(HEADER)

            # レースグループリンクの取得
            race_group_list = driver.find_elements_by_xpath('//ul[@class="CommonList_01"]/li/div/a')

            # レースグループ単位での処理
            for race_group_count in range(len(race_group_list)):
                # 開催日と開催場所の取得
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                date_and_venue: list[tuple[str, str]] = get_date_and_venue(soup)

                # レース一覧ページへの遷移
                trans_race_group_list = driver.find_elements_by_xpath('//ul[@class="CommonList_01"]/li/div/a')
                trans_race_group_list[race_group_count].click()
                sleep(1)

                # レース一覧ページのWebスクレイピング
                date_and_race_page_scraping(driver,
                                            date_and_venue[race_group_count],
                                            race_data_file)

                # レースグループ一覧ページへ戻る
                driver.get(race_group_url)
                sleep(1)

            # 次のレースグループ一覧ページへ遷移する
            if page_num < end_page_num:
                driver.find_element_by_link_text('次へ').click()
                sleep(1)
                race_group_url = driver.current_url

    except Exception as e:
        print('エラー発生!')
        print(driver.current_url)
        traceback.print_exc()
    finally:
        race_data_file.close()
        driver.quit()


if __name__ == '__main__':
    main()

