import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from data_loader import load_data

app = dash.Dash(__name__)

# Load initial data
df = load_data()
available_indices = sorted(df['Index_Name'].unique())

def calculate_percentage_changes(df, indices):
    intervals = [7, 14, 21, 30, 45, 90, 180, 365]
    results = []

    latest_date = df['Date'].max()

    for index in indices:
        index_df = df[df['Index_Name'] == index].sort_values('Date', ascending=False)
        if index_df.empty:
            continue

        latest_value = index_df.iloc[0]['Close_Index_Value']
        row = {'Index': index}

        for days in intervals:
            target_date = latest_date - pd.Timedelta(days=days)
            # Find the closest date before or on target_date
            past_data = index_df[index_df['Date'] <= target_date]

            if not past_data.empty:
                past_value = past_data.iloc[0]['Close_Index_Value']
                pct_change = ((latest_value - past_value) / past_value) * 100
                row[f'{days} Days'] = f"{pct_change:.2f}%"
            else:
                row[f'{days} Days'] = "N/A"
        results.append(row)

    return pd.DataFrame(results)

# Pre-calculate percentage changes
pct_change_df = calculate_percentage_changes(df, available_indices)

app.layout = html.Div([
    html.H1("Stock Indices Dashboard", style={'textAlign': 'center', 'marginBottom': '30px'}),

    # Top Section: Graph and Controls
    html.Div([
        # Left side: Graph
        html.Div([
            dcc.Loading(
                id="loading-graph",
                type="default",
                children=dcc.Graph(id='index-graph')
            )
        ], style={'width': '75%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        # Right side: Controls
        html.Div([
            html.Div([
                html.H3("Select Indices", style={'marginTop': '0'}),
                dcc.Checklist(
                    id='index-selector',
                    options=[{'label': i, 'value': i} for i in available_indices],
                    value=['Nifty50'] if 'Nifty50' in available_indices else [available_indices[0]],
                    labelStyle={'display': 'block', 'marginBottom': '5px'}
                ),
                html.Br(),
                html.H3("Select Days"),
                dcc.Dropdown(
                    id='days-selector',
                    options=[
                        {'label': '30 Days', 'value': 30},
                        {'label': '90 Days', 'value': 90},
                        {'label': '180 Days', 'value': 180},
                        {'label': '365 Days', 'value': 365},
                        {'label': 'All Data', 'value': 0}
                    ],
                    value=90,
                    clearable=False
                )
            ], style={
                'padding': '20px',
                'backgroundColor': '#f9f9f9',
                'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
            })
        ], style={'width': '22%', 'marginLeft': '2%', 'display': 'inline-block', 'verticalAlign': 'top'})
    ], style={'display': 'flex', 'marginBottom': '40px'}),

    # Bottom Section: Table
    html.Div([
        html.H2("Index Percentage Change", style={'textAlign': 'center', 'marginBottom': '20px'}),
        html.Div(id='table-container')
    ], style={'width': '100%'})
], style={'padding': '20px', 'fontFamily': 'Arial, sans-serif'})

@app.callback(
    [Output('index-graph', 'figure'),
     Output('table-container', 'children')],
    [Input('index-selector', 'value'),
     Input('days-selector', 'value')]
)
def update_dashboard(selected_indices, selected_days):
    if not selected_indices:
        return go.Figure(), html.Div("Please select at least one index.")

    filtered_df = df[df['Index_Name'].isin(selected_indices)]

    if selected_days > 0:
        latest_date = df['Date'].max()
        cutoff_date = latest_date - pd.Timedelta(days=selected_days)
        filtered_df = filtered_df[filtered_df['Date'] >= cutoff_date]

    fig = go.Figure()
    for index in selected_indices:
        index_df = filtered_df[filtered_df['Index_Name'] == index].sort_values('Date')
        fig.add_trace(go.Scatter(
            x=index_df['Date'],
            y=index_df['Close_Index_Value'],
            mode='lines',
            name=index
        ))

    fig.update_layout(
        title="Index Value Over Time",
        xaxis_title="Date",
        yaxis_title="Close Value",
        hovermode="x unified",
        margin={'l': 40, 'b': 40, 't': 40, 'r': 10},
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'right', 'x': 1}
    )

    table = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in pct_change_df.columns],
        data=pct_change_df.to_dict('records'),
        style_table={'overflowX': 'auto', 'border': '1px solid #ccc'},
        style_cell={'textAlign': 'left', 'padding': '12px', 'minWidth': '100px'},
        style_header={'backgroundColor': '#f4f4f4', 'fontWeight': 'bold', 'border': '1px solid #ccc'},
        style_data={'border': '1px solid #eee'}
    )

    return fig, table

if __name__ == '__main__':
    app.run(debug=True)
