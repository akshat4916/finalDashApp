import pandas as pd
import numpy as np
import plotly.express as px  # (version 4.7.0)
import plotly.graph_objects as go

import dash  # (version 1.12.0) pip install dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import json
from plotly.subplots import make_subplots


app = dash.Dash(__name__)
server = app.server

mapbox_access_token = "pk.eyJ1IjoiYWtzaGF0NDkxNiIsImEiOiJja25ocGtnMzEwbHE2Mndud3ltaXplZHlwIn0.OXr9v57gVzlsvXVniq_U-g"
mapbox_style = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"

# ---------- Import and clean data (importing csv into pandas)
YEARS = [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]

#df_first = pd.read_csv("first.csv")
#df_second = pd.read_csv("second.csv")

df_generated = pd.read_csv("generatedData.csv")


# ------------------------------------------------------------------------------
# App layout
app.layout = html.Div(
    id="root",
    children=[
        html.Div(
            id="header",
            style={"backgroundColor":"#222A2A",'color':'white','textAlign':'center'},
            children=[
                html.H1(children="Seniors Housing in Vancouver",
                    style={"paddingTop":'20px',"paddingBottom":'20px'}
                ),
            ],
        ),
        html.Div(
            id="app-container",
            children=[
                html.Div(
                    id="left_column",
                    children=[
                        html.Div(
                            id='slider',
                            children=[
                                dcc.Slider(
                                    id="slct_year",
                                    min=min(YEARS),
                                    max=max(YEARS),
                                    value=max(YEARS),
                                    marks={
                                        str(year): {
                                                "label": str(year),
                                                "style": {"color": "#7fafdf",'fontSize':14},
                                                }
                                                for year in YEARS
                                })
                            ]
                        )
                    ]
                ),
                html.Div(
                    id="row",
                    children=[
                        
                        html.Div(
                            id="Block2",
                            children=[
                                dcc.Graph(id='zip_pop_plot', figure={})
                            ],
                            style={
                                'width': '43%', 
                                'position':'absolute',
                                'display': 'inline-block',
                            }
                        ),
                        html.Div(
                            id="map_div",
                            children=[
                                html.Div(
                                    id='dropdown',
                                            children=[
                                                html.H2("Select the Value you want to see on the map:"),
                                                dcc.Dropdown(
                                                    id='dropdown_id',
                                                    options=[
                                                        {'label': 'Current Price', 'value': 'Current_Value'},
                                                        {'label': 'Current Maintenance Cost', 'value': 'Current_Maintenance'},
                                                        {'label': 'Senior Population Count', 'value': 'Senior Population'},
                                                        {'label': 'Number of Houses', 'value': 'Count'}
                                                    ],
                                                    value='Current_Value'
                                                ),
                                            ]
                                ),
                                html.Div(
                                    id="map1",
                                    children=[
                                        dcc.Graph(id='my_bee_map', figure={})
                                    ]
                                )
                            ],
                            style={'width': '50%', 'display': 'inline-block','margin-left':'47%'}
                        ),
                    ]
                ),
                html.Div(
                    id="charts",
                    children=[
                        
                        html.Div(
                            id="plots_div",
                            children=[dcc.Graph(id ='subplots',figure={})]
                        )
                    ]
                ),
            ])
    ]
)

#------------------------------------------------------------------------------
#Connect the Plotly graphs with Dash Components

@app.callback(
    
    Output(component_id='my_bee_map', component_property='figure'),
    [Input(component_id='slct_year', component_property='value'),
    Input(component_id='subplots',component_property='selectedData'),
    Input(component_id='dropdown_id',component_property='value')
    ]
)

def update_graph(year_selected,Category_selected,dropdownSelect):
    # print("----printing zipcodeselected")
    # print(zipCodeSelected)
    
    # print(dash.callback_context.inputs)
    # print(dash.callback_context.triggered)
    # print(dash.callback_context.states)

    ctx = dash.callback_context.inputs

    df = df_generated.copy()
    df = df[df["Year"] == year_selected]
    container = "The year chosen by user was: {}".format(year_selected)

    if(ctx['subplots.selectedData']!=None):
        #fetch the selected zipCode
        list_ofdictionaries = ctx['subplots.selectedData']['points']
        selectedCategory= []
        for i in list_ofdictionaries:
            selectedCategory.append(i['label'])

        #subset data for barplots
        df = df[df['Building_Category'].isin(selectedCategory)]

    # highest_priced = "$" + str(round(df['Current_Value'].max()))
    # median_price = "$" + str(round(df['Current_Value'].median()))

    if(dropdownSelect != "Count"):
        df[['Senior Population']] =df[["Senior Population"]].apply(pd.to_numeric) 
        df = df.groupby(['ZipCode']).agg({'Current_Value':'mean','Current_Maintenance':'mean','Senior Population': 'sum'}).reset_index()
    else:
        df = df.groupby(['ZipCode']).agg({'Current_Value':'count'}).reset_index()
        df.columns = ['ZipCode', 'Count']
    
    min_value = df[dropdownSelect].min()
    max_value = df[dropdownSelect].max()



    ##Choroplth maps
    with open("../bc.json") as geofile:
        geojson = json.load(geofile)

    fig = px.choropleth_mapbox(df, geojson=geojson, color=dropdownSelect,
                           locations="ZipCode", featureidkey="properties.CFSAUID",
                           center={"lat": 49.241017, "lon": -123.128545},
                           mapbox_style="carto-positron", zoom=10.5,range_color = [min_value,max_value],
                           color_continuous_scale=px.colors.sequential.GnBu)#YlGnBu)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(clickmode='event+select')
    


    return fig

@app.callback(
    
    Output(component_id='subplots', component_property='figure'),
    [Input(component_id='slct_year', component_property='value'),
    Input(component_id='my_bee_map',component_property='selectedData')]
)

def update_bar_plots(year_selected,my_bee_map):
    ctx = dash.callback_context.inputs
    ctx_triggered = dash.callback_context.triggered
    print(ctx_triggered)

    df = df_generated.copy()
    df = df[df["Year"] == year_selected]
    
    if(ctx['my_bee_map.selectedData']==None):

        ## Average data for current value
        df_current_value = df.groupby('Building_Category',as_index=False).mean()

        ##data frame change for %change for category
        df_population_change = df_generated.copy()
        df_population_change[["Senior Population"]] = df_population_change[["Senior Population"]].apply(pd.to_numeric)
        df_population_change = df_population_change.groupby(['Year','Building_Category'])['Senior Population'].sum().to_frame().reset_index()

        df_population_change['percent_change'] = df_population_change.groupby(['Building_Category'])['Senior Population'].pct_change()*100
        df_population_change['percent_change'] = df_population_change['percent_change'].fillna(0)
        
        df_population_change = df_population_change[df_population_change['Year']==year_selected]
        df_population_change["Color"] = np.where(df_population_change["percent_change"]<0, '#EF553B', '#00CC96')

    else:
        #fetch the selected zipCode
        list_ofdictionaries = ctx['my_bee_map.selectedData']['points']
        selectedZipCode = []
        for i in list_ofdictionaries:
            selectedZipCode.append(i['location'])

        #subset data for barplots
        df = df[df['ZipCode'].isin(selectedZipCode)]
        ## Average data for current value
        df_current_value = df.groupby('Building_Category',as_index=False).mean()

        ##data frame change for %change for category
        df_population_change = df_generated.copy()
        df_population_change = df_population_change[df_population_change['ZipCode'].isin(selectedZipCode)]
        df_population_change[["Senior Population"]] = df_population_change[["Senior Population"]].apply(pd.to_numeric)
        df_population_change = df_population_change.groupby(['Year','Building_Category'])['Senior Population'].sum().to_frame().reset_index()

        df_population_change['percent_change'] = df_population_change.groupby(['Building_Category'])['Senior Population'].pct_change()*100
        df_population_change['percent_change'] = df_population_change['percent_change'].fillna(0)
        
        df_population_change = df_population_change[df_population_change['Year']==year_selected]
        df_population_change["Color"] = np.where(df_population_change["percent_change"]<0, '#EF553B', '#00CC96')
        print(df_population_change.head())

    ##-----------Plots

    fig_bar1 = go.Bar(
        x=df_current_value['Building_Category'],
        y=df_current_value['Current_Value'],
        marker_color="#00CC96"
    )
    fig_bar2 = go.Bar(
        x=df_current_value['Building_Category'],
        y=df_current_value['Current_Maintenance'],
        marker_color="#00CC96"
    )
    fig_bar3 = go.Bar(
        x=df_population_change['Building_Category'],
        y=df_population_change['percent_change'],
        marker_color=df_population_change['Color']
    )
    fig1 = make_subplots(
        1,3,
        subplot_titles =(
            "<b>Average Selling Price vs<br> Building Category(for {})</b>".format(year_selected),
            "<b>Average Maintenance Cost vs<br> Building Category(for {})</b>".format(year_selected),
            "<b>Percentage Change in Seniors Population vs<br> Building Category(for {})</b>".format(year_selected)
        ),
        shared_xaxes=True
    )

    fig1.add_trace(
        fig_bar1,row=1,col=1
    )
    fig1.add_trace(
        fig_bar2,row=1,col=2
    )
    fig1.add_trace(
        fig_bar3,row=1,col=3
    )
    
    fig1.update_layout(showlegend = False)
    fig1.update_layout(clickmode='event+select')

    ##Axis labels
    fig1.update_xaxes(title_text="<b>Building Category</b>", row=1, col=1)
    fig1.update_xaxes(title_text="<b>Building Category</b>", row=1, col=2)
    fig1.update_xaxes(title_text="<b>Building Category</b>", row=1, col=3)
    fig1.update_yaxes(title_text="<b>Average Price</b>", row=1, col=1)
    fig1.update_yaxes(title_text="<b>Average Maintenance Cost</b>", row=1, col=2)
    fig1.update_yaxes(title_text="<b>Percentage Change</b>", row=1, col=3)
    return fig1


## For zip-population map
@app.callback(
    Output(component_id='zip_pop_plot', component_property='figure'),
    [
        Input(component_id='slct_year', component_property='value'),
        Input(component_id='subplots',component_property='selectedData')
    ]
)

def update_horizontal_plo(year_selected, Category_selected):
    ctx = dash.callback_context.inputs
    ctx_triggered = dash.callback_context.triggered

    df = df_generated.copy()
    #df = df[df["Year"] == year_selected]

    if(ctx_triggered[0]['prop_id'] == 'subplots.selectedData' and ctx_triggered[0]['value'] != None):
        #print(ctx_triggered[0]['value']['points'])
        selectedCategory= []
        list_ofdictionaries = ctx_triggered[0]['value']['points']
        for i in list_ofdictionaries:
            selectedCategory.append(i['label'])

        #subset data for barplots
        df = df[df['Building_Category'].isin(selectedCategory)]
    
    df[["Senior Population"]] = df[["Senior Population"]].apply(pd.to_numeric)
    df = df.groupby(['Year','ZipCode'])['Senior Population'].sum().to_frame().reset_index()

    df['percent_change'] = df.groupby(['ZipCode'])['Senior Population'].pct_change()*100
    df['percent_change'] = df['percent_change'].fillna(0)
        
    df = df[df['Year']==year_selected]
    df["Color"] = np.where(df["percent_change"]<0, '#EF553B', '#00CC96')

    df = df.sort_values(by=['percent_change'],ascending=False)
    df= df.head(5).append(df.tail(5))

    ##Plot
    fig_bar1 = go.Figure(go.Bar(
        x=df['percent_change'],
        y=df['ZipCode'],
        marker_color=df['Color'],
        orientation='h',
        text=df['percent_change'].astype(int),
        textposition='auto',
        textfont_color="white"
    ))
    fig_bar1.update_layout(autosize=False,height=580 )
    fig_bar1.update_yaxes(automargin=True)

    fig_bar1.update_layout(
        title={
            'text':"<b>Bottom 5 and Top 5 ZipCodes w.r.t Population Gain<br>(based on category selected)</b>",
            'xanchor':'left'
            },
        yaxis_title="<b>Zip Codes</b>",
        xaxis_title="<b>Percentage change in population from previous year</b>"
    )
    #fig_bar1 = px.bar(df, x='diff',y='ZipCode',orientation='h',color='Color')

    return fig_bar1

if __name__ == "__main__":
    app.run_server(debug=True)

