#!/usr/bin/python
# coding=utf-8
import requests
from io import StringIO
import pandas as pd
import numpy as np
import codecs
import datetime
import time
import sys
import locale
from locale import atof
import os
from argparse import ArgumentParser
import csv

MODE = "mon"
TW_STOCK_SERVER = "https://mops.twse.com.tw"
REFETCH = 1

# TODO: 找出今年配息, 殖利率等相關資訊
def get_html_dfs(stryear, strmonth):
    year = int(stryear)
    month = int(strmonth)
    monthly_file = "./mon_" + stryear + "_" + strmonth + ".html"
    if (0 != REFETCH):
        print("Refetch html..")
        open(monthly_file, 'a').close()
        os.remove(monthly_file)
    try:
        with open (monthly_file, 'r') as mf:
            dfs = pd.read_html(monthly_file, encoding='utf-8')
            print ("read html file successfully")
            return dfs
    except Exception as e:
        print(e)
        if year > 1990:
    	    year -= 1911
    
        url = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(month)+'_0.html'
        if year <= 98:
        	url = 'http://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(month)+'.html'
    
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    
        r = requests.get(url, headers=headers)
        r.encoding = 'big5'
        print ("fetch html file successfully")
        #print(url)
        #print(r.text)
    
        with codecs.open( monthly_file, mode='wb') as writefile:
            writefile.write(r.text.encode('utf8'))
        dfs = pd.read_html(StringIO(r.text), encoding='big-5')
        return dfs

def monthly_report(year, month):
    dfs = get_html_dfs(year, month)
    #print(dfs[1].describe)
    #print(dfs)

    df = pd.concat([df for df in dfs if df.shape[1] <= 11 and df.shape[1] > 5])
    #print(df.columns.tolist())
    
    if 'levels' in dir(df.columns):
        df.columns = df.columns.get_level_values(1)
    else:
        df = df[list(range(0,10))]
        column_index = df.index[(df[0] == '公司代號')][0]
        df.columns = df.iloc[column_index]

    #                0    1         2        3      4        5        6       7        8           9         10
    #df.columns = ["ID", "name", "income", "LMin", "LYMin", "MOM%", "YOY%",  "ACC",    "LYAcc",   "%AccYoY", "remark"]   #Before 2019/SEP
    df.columns  = ["ID", "name", "remark", "MOM%", "LMin",  "YOY%", "LYMin", "income", "%AccYoY", "LYAcc",   "ACC"]      #After  2019/SEP
    df['income'] = pd.to_numeric(df['income'], 'coerce')
    df = df[~df['income'].isnull()]
    df = df[df['ID'] != '合計']

    fake_fin_report = ['2489']
    major_job_ng = ['2363', '3018']

    blacklist = fake_fin_report
    blacklist += major_job_ng
    wlistcsv = csv.reader(open("white_list.txt"), delimiter=' ')
    wlist = list(zip(*wlistcsv))[0]

    #Directors and Supervisors 董監持股% 排行
    top_dshold_list = open("top_ds_holder_list.txt").read().splitlines()

    tdsh_df = wdf = df[df['ID'].isin(top_dshold_list) == True]
    print ("Top Directors & Supervisor Holding % List_________\n")

    #2019/SEP, column sequence changed:
    #print (wdf.iloc[0:25, [0,2,3,4,5,6,7,8,9,1,10]])
    print (wdf.iloc[0:25,  [0,7,4,6,3,5,10,9,8,1,2]])
    print ("\n")

    wdf = df[df['ID'].isin(wlist) == True]
    print ("White List_________\n")
    #print (wdf.iloc[0:25, [0,2,3,4,5,6,7,8,9,1,10]])
    print (wdf.iloc[0:25,  [0,7,4,6,3,5,10,9,8,1,2]])
    print ("\n")

    df = df[df['MOM%'] > 3]
    df = df[df['YOY%'] > 3]
    df = df[df['%AccYoY'] > 3.0]
    df = df[df['ID'].isin(blacklist) == False]
    df = df.sort_values(['%AccYoY'])
    #print ("df.columns")
    #print (df.columns)
    row_cnt, col_cnt = df.shape
    idx = 0
    while idx < row_cnt:
        print (str(year) + " " + str(month) + "th " + "monthly Good")
        #print (df.iloc[idx : idx+10, [0,2,3,4,5,6,7,8,9,1,10]])
        print (df.iloc[idx : idx+10, [0,7,4,6,3,5,10,9,8,1,2]])
        idx = idx + 10
    return df

def get_html_dfs_fin_stat(year, season, type):
    fin_stat_file = "./fin" + str(year) + "_" + str(season) + ".html"
    print ("Handle fin stat: " + fin_stat_file)
    if (0 != REFETCH):
        open(fin_stat_file, 'a').close()
        os.remove(fin_stat_file)
    try:
        with open (fin_stat_file, 'r') as fsf:
            dfs = pd.read_html(fin_stat_file, encoding='utf-8')
            print ("read html file successfully")
            return dfs
    except Exception as e:
        print(e)
        if year >= 1000:
            year -= 1911
            
        if type == '綜合損益彙總表':
            url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb04'
        elif type == '資產負債彙總表':
            url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb05'
        elif type == '營益分析彙總表':
            url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb06'
        else:
            print('type does not match')

        r = requests.post(url, {
            'encodeURIComponent':1,
            'step':1,
            'firstin':1,
            'off':1,
            'TYPEK':'sii',
            'year':str(year),
            'season':str(season),
        })

        r.encoding = 'utf8'
        print(r.text)
        dfs = pd.read_html(r.text)
        print ("fetch html file successfully")

        with codecs.open( fin_stat_file, mode='wb') as writefile:
            writefile.write(r.text.encode('utf8'))
        dfs = pd.read_html(StringIO(r.text), encoding='big-5')

        return dfs


# source:https://www.finlab.tw/Python-%E8%B2%A1%E5%A0%B1%E7%88%AC%E8%9F%B2-1-%E7%B6%9C%E5%90%88%E6%90%8D%E7%9B%8A%E8%A1%A8/
def financial_statement(year, season, type='綜合損益彙總表'):
    dfs = get_html_dfs_fin_stat(year, season, type)
    # 3rd df is the major table
    majordf = dfs[3]
    majordf = majordf.iloc[:, [0,    2,        3,       5,          10,     12,      13,            19,        20,    22,   29,    1     ] ]
    majordf.columns =         ["ID", "income", "Costs", "NetGross", "fees", "OpPft", "NonOpIn", "NetProf", "OCI", "CI", "EPS", "name"]


    # Gross Profit Margin rate
    di = {"--" : 0}
    majordf.income = majordf.income.map(di).fillna(majordf.income).astype(float)
    majordf.Costs = majordf.Costs.map(di).fillna(majordf.Costs).astype(float)
    majordf['gpm'] = (majordf.income.astype(float) - majordf.Costs.astype(float))/majordf.income.astype(float) * 100.0
    cols = majordf.columns.tolist()
    cols = cols[0:3] + cols[-1:] + cols[3:-1]
    #print(cols)
    majordf = majordf[cols]

    # Net Profit Margin rate
    di = {"--" : 0}
    majordf.NetProf = majordf.NetProf.map(di).fillna(majordf.NetProf).astype(float)
    majordf['npm'] = majordf.NetProf.astype(float) / majordf.income.astype(float) * 100.0
    cols = majordf.columns.tolist()
    cols = cols[0:9] + cols[-1:] + cols[9:-1]
    #print(cols)
    majordf = majordf[cols]

    majordf = majordf[majordf['EPS'] > 0.0]
    majordf = majordf[majordf['gpm'] > 5.0]
    majordf = majordf[majordf['npm'] > 5.0]
    white_list = monthly_report("108", "4")
    majordf = majordf.loc[majordf['ID'].isin(white_list['ID'])]

    # digit print format: 1,234,567
    for col in ['income', 'Costs','OpPft', 'NetProf', 'CI', 'NonOpIn']:
        majordf[col] = majordf.apply(lambda x: "{:,}".format(x[col]), axis=1)

    majordf = majordf.sort_values(['npm'])
    idx = 0
    row_cnt, col_cnt = majordf.shape
    while idx < row_cnt: 
        print ("\n" + str(year) + " season" + str(season) + "__" + str(idx) + " to " + str(idx+10))
        print(majordf[idx : idx+10])
        idx = idx + 10
    return True

#FIXME:
def get_daily_html(datestr):
    filename = datestr + ".txt"
    try:
        dfs = pd.read_html(filename, encoding='utf-8')
        print ("read html file successfully")
        return dfs
    except Exception as e:
        r = requests.post('http://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=' + datestr + '&type=ALL')
        with codecs.open( datestr + ".txt", mode='wb') as writefile:
            writefile.write(r.text.encode('utf8'))
        df = pd.read_csv(StringIO("\n".join([i.translate({ord(c): None for c in ' '}) 
                                     for i in r.text.split('\n') 
                                     if len(i.split('",')) == 17 and i[0] != '='])), header=0, thousands=',')
        return df


def daily_report(datestr):
    r = requests.post('http://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=' + datestr + '&type=ALL')
    with codecs.open( datestr + ".txt", mode='wb') as writefile:
        writefile.write(r.text.encode('utf8'))

    print("Date: " + datestr)
    df = pd.read_csv(StringIO("\n".join([line.translate({ord(c): None for c in ' '}) 
                                     for line in r.text.split('\n') 
                                     if len(line.split('",')) == 17 and line[0] != '='])), header=0, thousands=',')
    #print(df.columns.tolist())

    df = df.iloc[:, [0,    1,      2,            3,         4,       5,      6,      7,        8,       9,       10,     11,        12,      13,        14,      15  ] ]
    df.columns =    ["ID", "name", "DealShares", "DealCnt", "Deal$", "Open", "Peek", "Low", "Final", "Diff%", "Diff", "LBPrice", "LBAmt", "LSPrice", "LSAmt", "PERatio"]
    cols = df.columns.tolist()
    cols = cols[0:1] + cols[2:11] + cols[15:16] + cols[1:2]
    df = df[cols]

    '''
    # Translate non float strings
    #FIXME
    di = {"--" : 0, "4,455.00" : 4455.00, "4,365.00": 4365.00, "4,510.00":4510.00, "4,725.00":4725.00, "1,740.00":1740.00, "4,410.00":4410.00, "1,730.00":1730.00, "4,400.00": 4400.00}
    df.Peek=df.Peek.map(di).fillna(df.Peek).astype(float)
    df.Final=df.Final.map(di).fillna(df.Final).astype(float)
    df.Low=df.Low.map(di).fillna(df.Low).astype(float)

    #locale.setlocale(locale.LC_NUMERIC, '')
    #df.iloc[:,6:9].applymap(atof)

    # Find the strong ones
    strongIndex = (df['Final'] - df['Low']) / (df['Peek'] - df['Low'])
    print(strongIndex[(strongIndex > 0.8) & ((df['Peek'] / df['Low'] > 1.02))].sort_values(ascending=False))
    return
    '''

    gt3 = df[pd.to_numeric(df['PERatio'], errors='coerce') > 3]
    gt3lt10 = gt3[pd.to_numeric(df['PERatio'], errors='coerce') < 10]
    print(df.columns.tolist())
    print (strongIndex[:10])
    return df

def parse_commands():
    parser = ArgumentParser()
    subcmd = parser.add_subparsers()
    subcmd.required = True

    grp_twss = subcmd.add_parser('twss', help='TW stock server')
    grp_twss.add_argument("--mode", type=str, help="mon, fin, today, yesterday")
    # Server
    help_str = "TW stock server address, default = " + str(TW_STOCK_SERVER)
    grp_twss.add_argument("--twss_addr", type=str, help=help_str)
    grp_twss.add_argument("--refetch",   type=int, help="refetch the file")

    return parser.parse_args()

if __name__ == '__main__':
    # Handle Arguments
    args = parse_commands()
    print(args)

    if args.mode is not None:
        MODE = args.mode
    if args.twss_addr is not None:
        TW_STOCK_SERVER = str(args.twss_addr)
    if args.refetch is not None:
        REFETCH = args.refetch

    now = datetime.datetime.now()
    print("today:" + str(now.year) + " " + str(now.month) + " " + str(now.day))


    if ("today" == MODE):
        datestr = str(now.year) + str(now.month).zfill(2) + str(now.day-1).zfill(2)
        daily_report(datestr)
    elif ("yesterday" == MODE):
        datestr = str(now.year) + str(now.month).zfill(2) + str(now.day-2).zfill(2)
        daily_report(datestr)
    elif ("mon" == MODE):
        monthly_report("108", "9")
    elif ("fin" == MODE):
        try:
            financial_statement(108, 2)
            #if (True != financial_statement(108, 2)):
            #    financial_statement(108, 1)
        except Exception as e:
            print(e)

