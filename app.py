#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 10:50:28 2020

@author: nakhap
"""
import os, sys, re#, shutil
import sqlite3
import pandas as pd
import numpy as np
#from zipfile import ZipFile
from datetime import date 
import plotly.graph_objects as go
#import plotly.offline as offline
###############################################################################
def removUni(String):
    if isinstance(String, bytes):
        String = String.strip()
        return String.encode('ascii', 'ignore')#
    else:
        return String.strip()
#------------------------------------------------------------------------------
def getShortName(Mark, codeArray):
    Mark = removUni(Mark)
    m = re.findall('\d+|\D+', Mark)
    m = [i.strip() for i in m]
    try:
        ind = np.argwhere(codeArray[:,0]==m[0])
        return ' '.join(codeArray[ind,1][0].tolist() +[''.join(m[1:])])
    except IndexError:
        return Mark
#------------------------------------------------------------------------------
def getLongName(Mark, codeArray):
    Mark = removUni(Mark)
    m = re.findall('\d+|\D+', Mark)
    m = [i.strip() for i in m]
    try:
        ind = np.argwhere(codeArray[:,1]==m[0])
        if len(m) == 4:
            return ' '.join(codeArray[ind,0][0].tolist() +[''.join(m[1:3])]+[' '.join(m[3])])
        else:
            return ' '.join(codeArray[ind,0][0].tolist() +[''.join(m[1:])])
    except IndexError:
        return Mark
#------------------------------------------------------------------------------
def gesmarPassword():
    pf = open(r"V:\Business Unit\Operations\Location Data Services\Property Location\Survey Services\Scheduled Scripts\PWD1.txt")
    while True:
        line = pf.readline()
        return line.strip()
        if not line:
            break 
    pf.close()
#------------------------------------------------------------------------------
def IsNumber(value):
    "Checks if string is a number"
    try:
        float(value)
        check = True
    except:
        check = False
    return(check)
#------------------------------------------------------------------------------
def create_connection(db_file):
    """ create a database connection to a SQLite database """
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except:
        print ('Cannot create a database') 
    finally:
        conn.close() 
#------------------------------------------------------------------------------
def get_table_list(connection):
    curObj = connection.cursor()
    tableList = curObj.execute("SELECT NAME FROM sqlite_master WHERE TYPE = 'table'").fetchall()
    tableList = sum([list(x) for x in tableList],[])
    return tableList
#------------------------------------------------------------------------------
def getDuplicatesWithCount(listOfElems):
    ''' Get frequency count of duplicate elements in the given list '''
    dictOfElems = dict()
    # Iterate over each element in list
    for elem in listOfElems:
        # If element exists in dict then increment its value else add it in dict
        if elem in dictOfElems:
            dictOfElems[elem] += 1
        else:
            dictOfElems[elem] = 1    
 
    # Filter key-value pairs in dictionary. Keep pairs whose value is greater than 1 i.e. only duplicate elements from list.
    dictOfElems = { key:value for key, value in dictOfElems.items()}
    # Returns a dict of duplicate elements and thier frequency count
    return dictOfElems
#------------------------------------------------------------------------------
def build_banner():
    return html.Div(
        id="banner",
        className="banner",
        children=[
            html.Img(src=app.get_asset_url("LGGVCOM4.png")),
            html.H6("Landgate - Survey Services"),
        ],
    )
#------------------------------------------------------------------------------
def build_graph_title(title):
    return html.P(className="graph-title", children=title)
###############################################################################      
if __name__ == '__main__':
    ###########################################################################
    ####################### GOLA LOCAL DATABASE ###############################
    ###########################################################################
    workDir = os.getcwd()  
    dbname = os.path.join(workDir, "GolaLog_Metrix.v"+date.today().strftime('%Y')+".db")# "GolaLog_MetrixXXXX.accdb")
    if os.path.exists(dbname):
        conn = sqlite3.connect(dbname)
    else:
        print("No local gola database found")
        sys.exit()
    cursor = conn.cursor()  
    update_table_list = get_table_list(conn)
    #--------------------------------------------------------------------------
    # GESMAR Report 
    GesUpdateTable = "GES_Update_Report"
    if GesUpdateTable in update_table_list:
        gesCnt = pd.read_sql_query("SELECT * FROM "+GesUpdateTable+"", conn)
    GesAuthTable = "GES_AuthUpdate_Report"
    if GesAuthTable in update_table_list:
        gesAuthCnt = pd.read_sql("SELECT * FROM "+GesAuthTable+"", conn)
    #--------------------------------------------------------------------------
    # Prepare Dates & Query
    sqlQuery = []
    MonYear = []
    for tables in update_table_list:
        if tables.startswith("GOLA_Geodetic"):
            # Query
            sqlQuery.append("SELECT * FROM " + tables)
    # Fine tune query 
    sqlQuery = ' UNION ALL '.join(sqlQuery)
    sqlQuery = '( ' + sqlQuery + ') AS T'
    # Create a new table if not exist to store the ACCESS_DATES and MARK COUNTS
    CntTableName = "GOLA_Access_Report"
    if not CntTableName in update_table_list:
        cursor.execute("CREATE TABLE "+CntTableName+"(ACCESS_DATE DATE PRIMARY KEY, NO_OF_MARKS INTEGER)")
    
    df = pd.read_sql_query("SELECT ACCESS_DATE, POINT_NAME FROM "+sqlQuery+"", conn)
    df_copy = df.copy()

    df_copy.index = pd.to_datetime(df_copy['ACCESS_DATE'], format='%Y-%m-%d') 
    
    # Count the marks
    golaStatusCount = df_copy.groupby(pd.Grouper(freq='M')).count()['POINT_NAME']
    golaStatusCount.index = golaStatusCount.index.strftime('%Y-%m-01')
    # Update database
    toDatabase = pd.DataFrame(golaStatusCount).reset_index()
    toDatabase.columns = ['ACCESS_DATE', 'NO_OF_MARKS']
    toDatabase.to_sql(CntTableName, conn, if_exists='replace', index = False)
###############################################################################
########################## PLOTTING FIGURES ###################################
###############################################################################
    # Figure 1 - Get the count statistics
    golaCnt = pd.read_sql_query("SELECT * FROM "+CntTableName+"", conn)
    
    colors = ['cornflowerblue',] * len(df)
    colors[len(golaCnt)-1] = 'coral'
    fig = go.Figure()
    fig.add_trace(go.Bar(x=golaCnt['ACCESS_DATE'], y=golaCnt['NO_OF_MARKS'], 
                            text =["Date: "+a[:7]+"<br>Count: "+ str(b) for a, b in zip(golaCnt.ACCESS_DATE, golaCnt.NO_OF_MARKS)],
                            hoverinfo = "text",
                            marker_color=colors,
                            name = "GOLA ACCESS"
                            )) 
    fig.add_trace(go.Scatter(x=gesCnt['STATUS_DATE'], y=gesCnt['NO_OF_MARKS']*3, name='GESMAR UPDATES',
                              mode='lines+markers', 
                              line = dict(color='firebrick', width= 2),
                              text = ["Date: "+a[:7]+"<br>Count: "+ str(b) for a, b in zip(gesCnt.STATUS_DATE, gesCnt.NO_OF_MARKS)],
                              hoverinfo = "text"))
    fig.update_layout(
                    title = dict(text='<b>GOLA Station Summary Views & GESMAR Mark Updates</b>'),
                    xaxis_tickfont_size=14,
                    yaxis=dict(
                        title='Count per month',
                        titlefont_size=16,
                        tickfont_size=14,
                    ),
                    font=dict(
                        family="Courier New, monospace",
                        color="#7f7f7f",
                        size=16,
                        ),
                    width = 1000,
                    height = 500)
    fig.update_layout(
        legend = dict(x=0, y=1, traceorder="normal",
            font=dict(family="sans-serif", size=12, color="black"),
            bgcolor="LightSteelBlue",
            bordercolor="Black",
            borderwidth=2
            )
        )
    # fig.update_xaxes(rangeslider_visible=True)
    fig.update_layout(barmode='group', xaxis_tickangle=-45)
    # fig.show()
    # offline.plot(fig, auto_open=True,
    #             image_width=200, image_height=200, 
    #             filename='Barchart.html', validate=True)
    
    # Figure 2 - GESMAR Count By Authority
    fig2 = go.Figure()
    gesAuthCnt = gesAuthCnt[:40] # Pick the first 45 
    fig2.add_trace(go.Bar(x=gesAuthCnt['AUTHORITY'], y=gesAuthCnt['NO_OF_MARKS'], 
                          marker_color='coral',
                          text = ["Authority: "+a+"<br>Count: "+ str(b) for a, b in zip(gesAuthCnt.AUTHORITY, gesAuthCnt.NO_OF_MARKS)],
                          hoverinfo = "text"))
    fig2.update_traces(texttemplate=[str(x) for x in gesAuthCnt['NO_OF_MARKS']], textposition='outside')
    fig2.update_layout(
                title = dict(
                    text='<b>GOLA Station Summary Views by Authority</b>'),
                yaxis=dict(
                    title='Number of Marks', titlefont_size=16,tickfont_size=14,
                    ),
                xaxis=dict(
                    title='Authority Names', titlefont_size=16,tickfont_size=14,
                    ),
                font=dict(
                    family="Courier New, monospace",
                    color="#7f7f7f",
                    size=16,
                    ),
                width = 1000,
                height = 500)
    # Figure 3 - Spatial map
    data_slider = []
    textprint = []
    for mony in golaCnt.ACCESS_DATE:
        mony = mony[:7]
        theMarks = pd.read_sql_query("SELECT POINT_NAME, POINT_TYPE, LATITUDE, LONGITUDE, COUNT(POINT_NAME) AS COUNTS \
                                      FROM "+sqlQuery+" WHERE ACCESS_DATE LIKE '"+mony+"%' \
                                    GROUP BY POINT_NAME ", conn)
        pname = theMarks['POINT_NAME']
        pname = [x.replace('&','&amp;').replace('/','&#47;').replace('(','&#40;').replace(')','&#41;') for x in pname]
        theMarks['text'] = pd.Series(pname) +  '<br>COUNT: '+ theMarks['COUNTS'].astype(str)
        data_one_month = dict(
                        type = 'densitymapbox',
                        lat=theMarks.LATITUDE, 
                        lon=theMarks.LONGITUDE, 
                        z=theMarks.COUNTS,
                        radius=7,
                        colorscale = "Viridis",
                        text = [x for x in theMarks.text],
                        texttemplate = "%{text}",
                        textposition = "bottom center",
                        hoverinfo ="text",
                        )
        data_slider.append(data_one_month)
        textprint.append([x.replace('&','&amp;') for x in theMarks.text]) 
    steps = []
    for i in range(len(data_slider)):
        step = dict(method='restyle',
                    args=['visible', [False] * len(data_slider)],
                    label= golaCnt.ACCESS_DATE[i][:7]) # label to be displayed for each step (year)
        step['args'][1][i] = True
        steps.append(step)
        
    sliders = [dict(active=0, pad={"t": 10}, steps=steps)] 
    mapbox_access_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNqdnBvNDMyaTAxYzkzeW5ubWdpZ2VjbmMifQ.TXcBE-xg9BFdV2ocecc_7g"
  
    layout = dict(
            title = dict(text='<b>Heat map of marks whose station summaries were viewed in GOLA</b>'),
            font=dict(
                    family="Courier New, monospace",
                    color="#7f7f7f",
                    size=16,
                    ),             
  			dragmode= 'zoom',
 			#mapbox= { 'style': "satellite", 'accesstoken': mapbox_access_token, 'center': { 'lat': -26, 'lon': 122 }, 'zoom': 4.5 },
            mapbox= { 'style': "open-street-map",'center': { 'lat': -26, 'lon': 122 }, 'zoom': 4.5 },
 			margin= { 'r': 50, 't': 50, 'b': 50, 'l': 10 },
            sliders= sliders,
            height= 1000,
		)
    fig3 = dict(data=data_slider, layout=layout)    
    # scl = [[0.0, '#ffffff'],[0.2, '#ff9999'],[0.4, '#ff4d4d'], \
    #    [0.6, '#ff1a1a'],[0.8, '#cc0000'],[1.0, '#4d0000']] # reds
    # fig3 = go.Figure(go.Densitymapbox(lat=theMarks.LATITUDE, lon=theMarks.LONGITUDE, z=theMarks.COUNTS,
    #                              radius=7, 
    #                              text= theMarks.text, 
    #                              hoverinfo = "text"))
    # fig3.update_layout(mapbox_style="open-street-map", mapbox_center_lon=122, mapbox_center_lat=-26, mapbox_zoom=4.5)
    # fig3.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=1000)
    
    import dash
    import dash_core_components as dcc
    import dash_html_components as html
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    server = app.server
    
    app.layout = html.Div(
        children = [
            html.Div(
                id="top-row",
                children = [
                    html.H1(
                        children="Landgate Survey Services",
                        style={
                        'textAlign': 'center',
                        'color': '#000080'
                        }),
                    ]
                ),
            html.Div(
                id="second-row",
                children= [
                    html.H2(
                        children = "Geodetic Report: GOLA access summary & GESMAR updates.",
                        style={
                        'textAlign': 'center',
                        'color': '#000080'
                        }),
                    ]
                ),
            html.Div([
                dcc.Graph(id='GOLA views & GESMAR updates', 
                          figure=fig,
                ),
                dcc.Graph(id='authority-map', 
                          figure=fig2,
                ),
            ], style={'display': 'inline-block', 'width': '49%'}),
            html.Div([
                dcc.Graph(
                    id='spatial-map',
                    figure=fig3,
                )
            ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 10'}),
            ]
        )
    
    app.run_server()  # Turn off reloader if inside Jupyter
