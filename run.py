import plotly.graph_objects as go # or 
import plotly.express as px
import pandas as pd
import numpy as np

from koboextractor import KoboExtractor
import tweepy
import requests
from collections import Counter

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output

port = 465  # For SSL
password = "XXXXXXXXXXXXXX"
smtp_server = "smtp.gmail.com"
sender_email = "tobi.shivang@gmail.com"  # Enter your address
receiver_email = "writetoshivang@gmail.com"  # Enter receiver address

app = dash.Dash(__name__)

def twitterAPI():
    API_key = 'enter_api_key_here'
    API_secretKey = 'enter_api_secret_here'

    AccessToken = 'enter_access_token_here'
    Access_Token_Secret = 'enter_access_token_here'

    auth = tweepy.OAuthHandler(API_key, API_secretKey)
    auth.set_access_token(AccessToken, Access_Token_Secret)

    api = tweepy.API(auth)
    return api
#-------------------------------------------------------------------------------


def update_task():
    kobo = KoboExtractor('enter_kobo_key_here', 'https://kobo.humanitarianresponse.info/api/v2')
    #assets = kobo.list_assets()
    asset_uid = kobo.list_assets()['results'][0]['uid']
    #new_data = kobo.get_data(asset_uid)
    newdata = kobo.get_data(asset_uid)['results']
    df = pd.read_json (r'olddata.json')
    global df_update
    df_update = pd.DataFrame(columns =['Complaint ID', 'Issue', 'Report Time', 'City','District','State','Longitude','Latitude','Description'], dtype=object)
    if len(newdata) != len(df.index):
        for i in newdata:
            if i['_id'] not in list(df['Complaint ID']):
                coord = i['_geolocation']
                #print(coord)
                params = (
                    ('at', str(coord[0])+","+str(coord[1])),
                    ('q', 'police+station'),
                    ('apiKey', 'sd75vPgJimA3mXT-FxMLqup8DkAeukQ834U2jY3-R1o')
                )

                locationdata = requests.get('https://discover.search.hereapi.com/v1/discover', params=params).json()
                try:
                    statepoint = locationdata['items'][0]['address']['state']
                    citypoint = locationdata['items'][0]['address']['city']
                    distpoint = locationdata['items'][0]['address']['district']
                except KeyError:
                    distpoint = ''
                df_update.loc[len(df.index)] = [i['_id'], i['Select_the_issue_type'], i['_submission_time'],citypoint,distpoint,statepoint,coord[1],coord[0],i['Complaint_description']]
                df.loc[len(df.index)] = [i['_id'], i['Select_the_issue_type'], i['_submission_time'],citypoint,distpoint,statepoint,coord[1],coord[0],i['Complaint_description']]
                message = '@covid_stateIGW - A complaint has been registered from '+citypoint+','+distpoint+','+statepoint+ ' with the description: '+i['Complaint_description']
                '''
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                    server.login(sender_email, password)
                    server.sendmail(sender_email, receiver_email, message)
                #twitterAPI().update_status(message)
                '''
        df.to_json("olddata.json")
    df1 = df.sort_values(by=['Complaint ID'], ascending=False)
    mapbox_access_token = "pk.enter_map_token_here"
    df_update = df_update.reset_index()
    del df_update['index']

    global new
    new = df1
    new = new.reset_index()
    del new['index']
    new["DateTime"] = pd.to_datetime(new["Report Time"])
    new['Date'] = new['DateTime'].dt.normalize()

    global trace_1
    trace_1 = go.Scattermapbox(
                name='Old ' + '<br>' +'Complaints',
                lat=new['Latitude'],
                lon=new['Longitude'],
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=8,
                    color='fuchsia',
                    opacity=0.7,
                    #hover_name = 'Issue'
                ),
                showlegend = True,
                text=[new['City'][i] + 
                '<br>' +new['District'][i] + 
                '<br>' + new['State'][i] 
                for i in range(new.shape[0])],
            )
            
            
    global layout
    layout = go.Layout(title='Geolocation of Complaints',
                    autosize=True,
                    width=1680,
                    height=800,
                    hovermode='closest',
                    mapbox_style='dark',
                    mapbox=dict(
                    accesstoken=mapbox_access_token,
                    bearing=0,
                    center=dict(
                    lat=20.5937,
                    lon=78.9629
                    ),
                    pitch=0,
                    zoom=4,
            ),
            )
    fig = go.Figure(data = [trace_1], layout = layout)



    time = []
    t = df['Report Time']
    for i in t:
        time.append(i[:10])


    # In[4]:


    


    # In[9]:


    ReportTime = Counter(time)
    df2 = pd.DataFrame.from_dict(ReportTime, orient='index').reset_index()
    df2 = df2.rename(columns={'index':'Day', 0:'No of complaints'})
    df2 = df2.sort_values(by=['Day'], ascending=False)

    fig2 = px.line(df2, x = 'Day', y = 'No of complaints', title='Line Graph showing compliants per day')


    # In[12]:


    issuelist = df['Issue']
    issuescount = Counter(issuelist)
    df3 = pd.DataFrame.from_dict(issuescount, orient='index').reset_index()
    df3 = df3.rename(columns={'index':'Issues', 0:'count'})
    #df2
    fig3 = px.pie(df3, values='count', names='Issues', title='Pie Chart showing complaints as per type of issue')

    statelist = df[['Report Time','State','Issue']]
    statelist = statelist.reset_index()
    #statelist
    statecount = statelist.groupby(by='State').count()
    statelist['freq']=statelist.groupby(by='State')['State'].transform('count')

    statelist['Report Time'] = pd.to_datetime(statelist['Report Time']).dt.date
    fig4 = px.scatter(statelist, x="State", y="freq",size="freq", color="freq", log_x= False, size_max=60)
    
    return([
            html.Div( children = [
                        # adding a header and a paragraph
                        html.Div([
                            html.H1("Complaint Portal"),
                            html.P("Let's help People!!")
                                ], 
                            style = {'padding' : '50px' , 
                                    'backgroundColor' : '#3aaab2'}),
            ##dropdown
                        html.Div(
                        children=[
                            html.Div(
                                children=[
                                    html.Div(children="City", className="menu-title"),
                                        dcc.Dropdown(
                                            id="City-filter",
                                            options=[
                                                {"label": City, "value": City}
                                                for City in np.sort(new.City.unique())
                                            ],
                                            value="Delhi",
                                            clearable=False,
                                            className="dropdown",
                                            ),
                                        ],style = {'width': '400px','fontSize' : '15px','padding-left' : '100px', 'display': 'block'}
                                    ),
                            html.Div(
                                children=[
                                    html.Div(children="Issue", className="menu-title"),
                                    dcc.Dropdown(
                                        id="Issue-filter",
                                        options=[
                                            {"label": Issue, "value": Issue}
                                            for Issue in new.Issue.unique()
                                        ],
                                        value="Covid_emergency",
                                        clearable=False,
                                        searchable=False,),
                                        ],style = {'width': '400px','fontSize' : '15px','padding-left' : '100px','display': 'block'}
                                ),
                            html.Div(
                                children=[
                                    html.Div(
                                        children="Date Range",
                                        className="menu-title"
                                            ),
                                    dcc.DatePickerRange(
                                        id="date-range",
                                        min_date_allowed=new.Date.min().date(),
                                        max_date_allowed=new.Date.max().date(),
                                        start_date=new.Date.min().date(),
                                        end_date=new.Date.max().date(),
                                            ),
                                        ], style={'width': '400px','fontSize' : '15px','padding-left' : '100px','display': 'block'}
                                    ),
                            html.Div(children=["FILTERED COMPLAINTS",
                                        ],
                                        style={'color':'white','width': '400px','margin-left': '6vw','margin-top': '2vw','fontSize' : '20px','display': 'block'}
                                    ),        
                            html.Div(children=[
                                dash_table.DataTable(id='table', columns = [{"name": i, "id": i} 
                                    for i in new.loc[:,['Complaint ID','Issue','Report Time']]],data=[],
                                        style_cell=dict(textAlign='right'),
                                        style_header=dict(backgroundColor="paleturquoise"),
                                        style_data=dict(backgroundColor="lavender")),
                            ],style={'width': '400px','margin-left': '6vw','fontSize' : '15px','display': 'block','overflow': 'scroll'}
                            ),
                        ],style={'position': 'absolute','z-index': '6','margin-top': '6vw', 'display': 'inline-block'}),

                    
                    ##plot 
                    html.Div(
                        children=[
                        dcc.Graph(id="plot", figure = fig),
                        ]),               
        ],style={'vertical-align': 'top', 'margin-left': '0vw','margin-top': '-1.5vw'}),
        
            html.Div(children=[
            html.Div(children=[  
            dcc.Graph(figure=fig3),
            ],style={'display': 'inline-block','vertical-align': 'ytop', 'margin-left': '4vw', 'margin-top': '2vw','maxHeight': '650px'}),
            html.Div(children=[
            html.Div(id="newtable", children=["NEW COMPLAINTS",
                dash_table.DataTable(
                    id='table1',
                    columns=[{"name": i, "id": i}
                            for i in df_update.loc[:,['Complaint ID','Issue','State','Report Time']]],
                    data=df_update.to_dict('records'),
                    style_cell=dict(textAlign='right'),
                    style_header=dict(backgroundColor="paleturquoise"),
                    style_data=dict(backgroundColor="lavender")
                )
                ],style={'display': 'block', 'horizontal-align': 'top', 'margin-top': '0vw','maxHeight': '150px','overflow': 'scroll'}),
                html.Div(id="totaltable", children=["TOTAL COMPLAINTS",
                dash_table.DataTable(
                    id='table2',
                    columns=[{"name": i, "id": i} 
                            for i in df1.loc[:,['Complaint ID','Issue','State','Report Time']]],
                    data=df1.to_dict('records'),
                    style_cell=dict(textAlign='right'),
                    style_header=dict(backgroundColor="paleturquoise"),
                    style_data=dict(backgroundColor="lavender")
                )
                ],style={'display': 'block', 'horizontal-align': 'top', 'margin-top': '1vw','maxHeight': '500px','overflow': 'scroll'})
                ],style={'display': 'inline-block','position': 'absolute', 'horizontal-align': 'top','vertical-align': 'ytop', 'margin-left': '4vw', 'margin-top': '2vw','maxHeight': '650px'}),
            ]),
            html.Div(id="plot24", children=[
            dcc.Graph(figure=fig2),
            dcc.Graph(figure=fig4)]),
    ])
#-------------------------------------------------------------------------------
app.layout = html.Div([
                dcc.Interval
                (
                    id='my_interval',
                    disabled=False,     #if True the counter will no longer update
                    n_intervals=0,      #number of times the interval has passed
                    interval=300*1000,  #increment the counter n_intervals every 5 minutes
                    max_intervals=-1,  #number of times the interval will be fired.
                                        #if -1, then the interval has no limit (the default)
                                        #and if 0 then the interval stops running.
                ),

                html.Div
                ([
                    html.Div(id="plots", children=update_task())
                ]),

            ])

#-------------------------------------------------------------------------------
# Callback to update news
@app.callback(Output("plots", "children"), [Input("my_interval", "n_intervals")])
def update_task_div(n):
    return update_task()

@app.callback(
    [Output("plot", "figure"),Output("table", "data")],
    [
        Input("City-filter", "value"),
        Input("Issue-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)


def update_charts(City, Issue, start_date, end_date):

    mask = (
        (new.City == City)
        & (new.Issue == Issue)
        & (new.Date >= start_date)
        & (new.Date <= end_date)
    )
    filtered_data = new.loc[mask, :]
    filtered_data = filtered_data.reset_index()
    del filtered_data['index']
    
    trace_2 = go.Scattermapbox(
            name='selected ' + '<br>' +'Complaints',
            lat=filtered_data['Latitude'],
            lon=filtered_data['Longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=10,
                color='yellow',
                opacity=0.7,
                #hover_name = 'Issue'
            ),
            showlegend = True,
            text=[filtered_data['City'][i] + 
            '<br>' +filtered_data['District'][i] + 
            '<br>' + filtered_data['State'][i] 
            for i in range(filtered_data.shape[0])],
        )

    fig = go.Figure(data = [trace_1,trace_2], layout = layout)
    
    
    if len(df_update)!= 0: 
        fig.add_trace(
            go.Scattermapbox(
            name='New ' + '<br>' +'Complaints',
            lat=df_update['Latitude'],
            lon=df_update['Longitude'],
            #hover_name="Issue",
            #hover_data=['Report Time', 'City','District','State'],
            #color_discrete_sequence=["yellow"],zoom=9),
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=14,
                color='red',
                #hover_name = 'Issue'
                ),
            showlegend = True,
            text=[df_update['City'][i] + 
            '<br>' + df_update['District'][i] + 
            '<br>' + df_update['State'][i] 
            for i in range(len(df_update))],
            )
        )
    data_ob = filtered_data.to_dict('records')
    
    return fig , data_ob
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)



