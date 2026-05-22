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
    html.H1("Stock Indices Dashboard", style={'textAlign': 'center'}),

    html.Div([
        # Left side: Graph and Table
        html.Div([
            dcc.Graph(id='index-graph'),
            html.Div(id='table-container')
        ], style={'width': '75%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        # Right side: Controls
        html.Div([
            html.H3("Select Indices"),
            dcc.Checklist(
                id='index-selector',
                options=[{'label': i, 'value': i} for i in available_indices],
                value=['Nifty50'] if 'Nifty50' in available_indices else [available_indices[0]],
                labelStyle={'display': 'block'}
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
        ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '20px', 'backgroundColor': '#f9f9f9'})
    ], style={'display': 'flex'})
])

@app.callback(
    [Output('index-graph', 'figure'),
     Output('table-container', 'children')],
    [Input('index-selector', 'value'),
     Input('days-selector', 'value')]
)
def update_graph(selected_indices, selected_days):
    if not selected_indices:
        return go.Figure()

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
        hovermode="x unified"
    )

    table = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in pct_change_df.columns],
        data=pct_change_df.to_dict('records'),
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
    )

    return fig, [html.H3("Percentage Change Over Intervals"), table]

if __name__ == '__main__':
    app.run(debug=True)
