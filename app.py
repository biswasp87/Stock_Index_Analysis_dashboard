import dash
from dash import dcc, html, Input, Output
import dash_ag_grid as dag
import plotly.graph_objs as go
import pandas as pd
from data_loader import load_data, load_equity_data, get_index_constituents, calculate_pct_changes

# dangerously_allow_code=True is required for using JavaScript functions in column definitions
app = dash.Dash(__name__)

# Load data
df_indices = load_data()
df_equity = load_equity_data()
constituents_map = get_index_constituents()

# Calculate changes
indices_changes = calculate_pct_changes(df_indices, 'Index_Name', 'Close_Index_Value')
equity_changes = calculate_pct_changes(df_equity, 'Stock_Symbol', 'Close_Value')

# Prepare Master-Detail Data
master_data = []
for _, row in indices_changes.iterrows():
    index_name = row['Name']
    constituents = constituents_map.get(index_name, [])
    detail_data = equity_changes[equity_changes['Name'].isin(constituents)].to_dict('records')
    master_row = row.to_dict()
    master_row['constituents'] = detail_data
    master_data.append(master_row)

# Color scale function in JS
color_scale_js = """
function(params) {
    if (params.value == null) return {};
    if (params.value > 0) {
        const alpha = Math.min(params.value / 10, 1) * 0.7 + 0.1;
        return {backgroundColor: `rgba(0, 255, 0, ${alpha})`, color: 'black'};
    } else if (params.value < 0) {
        const alpha = Math.min(Math.abs(params.value) / 10, 1) * 0.7 + 0.1;
        return {backgroundColor: `rgba(255, 0, 0, ${alpha})`, color: alpha > 0.5 ? 'white' : 'black'};
    }
    return {};
}
"""

common_col_defs = [
    {"field": "7d", "headerName": "7 Days"},
    {"field": "14d", "headerName": "14 Days"},
    {"field": "21d", "headerName": "21 Days"},
    {"field": "30d", "headerName": "30 Days"},
    {"field": "45d", "headerName": "45 Days"},
    {"field": "90d", "headerName": "90 Days"},
    {"field": "180d", "headerName": "180 Days"},
    {"field": "365d", "headerName": "365 Days"},
]

for col in common_col_defs:
    col["valueFormatter"] = {"function": "params.value != null ? params.value.toFixed(2) + '%' : 'N/A'"}
    col["cellStyle"] = {"function": color_scale_js}
    col["sortable"] = True

column_defs = [
    {"field": "Name", "headerName": "Index", "cellRenderer": "agGroupCellRenderer", "pinned": "left", "sortable": True},
] + common_col_defs

detail_column_defs = [
    {"field": "Name", "headerName": "Stock", "pinned": "left", "sortable": True},
] + common_col_defs

app.layout = html.Div([
    html.H1("Expandable Stock Indices Dashboard", style={'textAlign': 'center'}),

    html.Div([
        html.Div([dcc.Graph(id='index-graph')], style={'width': '75%'}),
        html.Div([
            html.H3("Filters"),
            dcc.Checklist(id='index-selector', options=[{'label': k, 'value': k} for k in constituents_map.keys()], value=['Nifty50']),
            html.Br(),
            dcc.Dropdown(id='days-selector', options=[{'label': f'{d} Days', 'value': d} for d in [30, 90, 180, 365]], value=90)
        ], style={'width': '23%', 'padding': '20px', 'backgroundColor': '#f9f9f9'})
    ], style={'display': 'flex'}),

    html.Div([
        html.H2("Performance Table (Expand rows to see constituents)"),
        dag.AgGrid(
            id="expandable-table",
            columnDefs=column_defs,
            rowData=master_data,
            masterDetail=True,
            detailCellRendererParams={
                "detailGridOptions": {
                    "columnDefs": detail_column_defs,
                    "defaultColDef": {"resizable": True, "sortable": True}
                },
                "detailColName": "constituents",
            },
            defaultColDef={"resizable": True, "filter": True, "sortable": True},
            style={"height": "600px", "width": "100%"},
            dangerously_allow_code=True,
            enableEnterpriseModules=True
        )
    ])
], style={'padding': '20px'})

@app.callback(
    Output('index-graph', 'figure'),
    [Input('index-selector', 'value'), Input('days-selector', 'value')]
)
def update_graph(selected_indices, selected_days):
    if not selected_indices: return go.Figure()
    filtered = df_indices[df_indices['Index_Name'].isin(selected_indices)]
    if selected_days > 0:
        cutoff = df_indices['Date'].max() - pd.Timedelta(days=selected_days)
        filtered = filtered[filtered['Date'] >= cutoff]
    fig = go.Figure()
    for idx in selected_indices:
        d = filtered[filtered['Index_Name'] == idx].sort_values('Date')
        fig.add_trace(go.Scatter(x=d['Date'], y=d['Close_Index_Value'], name=idx, mode='lines'))
    return fig

if __name__ == '__main__':
    app.run(debug=True)
