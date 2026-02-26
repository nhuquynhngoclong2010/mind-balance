import plotly.graph_objects as go
import pandas as pd
import json


def _parse_tasks(x):
    """Parse tasks an toàn — xử lý cả list và string JSON từ Supabase"""
    if isinstance(x, list):
        return len(x)
    if not x or str(x).strip() in ('', 'None', 'null'):
        return 0
    try:
        return len(json.loads(str(x)))
    except Exception:
        return 0


def _safe_numeric(series):
    """Convert series sang numeric an toàn"""
    return pd.to_numeric(series, errors='coerce').fillna(0)


def create_energy_trend(df):
    """Biểu đồ xu hướng năng lượng"""
    df = df.copy()
    df = df[df['date'].astype(str).str.len() == 10].reset_index(drop=True)
    if len(df) == 0:
        return go.Figure()
    df['energy_level'] = _safe_numeric(df['energy_level'])

    df['date'] = df['date'].astype(str)
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['energy_level'],
        mode='lines+markers',
        name='Năng lượng',
        line=dict(
            color='rgba(255, 140, 66, 0.9)',
            width=4,
            shape='spline'
        ),
        marker=dict(
            size=16,
            color='rgba(255, 140, 66, 1)',
            line=dict(color='white', width=3),
            symbol='circle'
        ),
        fill='tozeroy',
        fillcolor='rgba(255, 140, 66, 0.15)',
        hovertemplate='<b>%{x}</b><br>Năng lượng: %{y}/10<extra></extra>'
    ))

    fig.update_layout(
        title={
            'text': '🦊 Xu hướng năng lượng trong tuần',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 22, 'family': 'Poppins, sans-serif', 'color': 'white'}
        },
        xaxis=dict(
            title=dict(text='Ngày', font=dict(size=14)),
            tickfont=dict(size=13, color='white'),
            showgrid=True,
            gridcolor='rgba(255,255,255,0.2)',
            color='white'
        ),
        yaxis=dict(
            title=dict(text='Mức năng lượng', font=dict(size=14)),
            range=[0, 11],
            tickfont=dict(size=13, color='white'),
            showgrid=True,
            gridcolor='rgba(255,255,255,0.2)',
            color='white'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Quicksand, sans-serif', size=13),
        hovermode='x unified',
        margin=dict(t=60, b=40, l=40, r=40)
    )

    return fig


def create_task_energy_comparison(df):
    """So sánh số công việc vs năng lượng"""
    df = df.copy()
    df = df[df['date'].astype(str).str.len() == 10].reset_index(drop=True)
    if len(df) == 0:
        return go.Figure()
    df['energy_level'] = _safe_numeric(df['energy_level'])
    df['task_count'] = df['tasks'].apply(_parse_tasks)

    df['date'] = df['date'].astype(str)
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['task_count'],
        name='Số công việc',
        marker=dict(
            color='rgba(240, 147, 251, 0.8)',
            line=dict(color='rgba(240, 147, 251, 1)', width=2)
        ),
        text=df['task_count'],
        textposition='outside',
        textfont=dict(size=13, color='white'),
        hovertemplate='<b>%{x}</b><br>Công việc: %{y}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['energy_level'],
        name='Năng lượng',
        mode='lines+markers',
        yaxis='y2',
        line=dict(color='#FF8C42', width=4, shape='spline'),
        marker=dict(size=12, color='#FF8C42', line=dict(color='white', width=3)),
        hovertemplate='<b>%{x}</b><br>Năng lượng: %{y}/10<extra></extra>'
    ))

    fig.update_layout(
        title={
            'text': '📋🦊 Công việc vs Năng lượng',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 22, 'family': 'Poppins, sans-serif', 'color': 'white'}
        },
        xaxis=dict(
            title=dict(text='Ngày', font=dict(size=14)),
            tickfont=dict(size=13, color='white'),
            showgrid=True,
            gridcolor='rgba(255,255,255,0.2)',
            color='white'
        ),
        yaxis=dict(
            title=dict(text='Số công việc', font=dict(size=14)),
            tickfont=dict(size=13, color='white'),
            showgrid=True,
            gridcolor='rgba(255,255,255,0.2)',
            color='white'
        ),
        yaxis2=dict(
            title=dict(text='Mức năng lượng', font=dict(size=14)),
            tickfont=dict(size=13, color='white'),
            overlaying='y',
            side='right',
            range=[0, 11],
            showgrid=False,
            color='white'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Quicksand, sans-serif', size=13),
        barmode='group',
        hovermode='x unified',
        legend=dict(
            bgcolor='rgba(255,255,255,0.15)',
            bordercolor='rgba(255,255,255,0.4)',
            borderwidth=2,
            font=dict(color='white', size=13)
        ),
        margin=dict(t=60, b=40, l=40, r=60)
    )

    return fig


def create_mood_matrix(df):
    """Ma trận tâm trạng - Áp lực vs Năng lượng"""
    df = df.copy()
    df = df[df['date'].astype(str).str.len() == 10].reset_index(drop=True)
    if len(df) == 0:
        return go.Figure()
    df['energy_level'] = _safe_numeric(df['energy_level'])

    mental_load_map = {
        'Nhẹ nhàng': 1,
        'Bình thường': 2,
        'Nặng': 3,
        'Cực nặng': 4
    }

    df['mental_load_numeric'] = df['mental_load'].map(mental_load_map).fillna(2)

    colors = []
    for energy in df['energy_level']:
        if energy <= 3:
            colors.append('#f5576c')
        elif energy <= 6:
            colors.append('#f093fb')
        else:
            colors.append('#FF8C42')

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['mental_load_numeric'],
        y=df['energy_level'],
        mode='markers+text',
        text=df['date'],
        textposition='top center',
        textfont=dict(color='white', size=11),
        marker=dict(
            size=20,
            color=colors,
            line=dict(color='white', width=3)
        ),
        hovertext=df['date'],
        hovertemplate='<b>%{hovertext}</b><br>Áp lực: %{x}<br>Năng lượng: %{y}/10<extra></extra>'
    ))

    fig.update_layout(
        title={
            'text': '🎯🦊 Ma trận Áp lực vs Năng lượng',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 22, 'family': 'Poppins, sans-serif', 'color': 'white'}
        },
        xaxis=dict(
            title=dict(text='Mức độ áp lực tinh thần', font=dict(size=14)),
            tickmode='array',
            tickvals=[1, 2, 3, 4],
            ticktext=['Nhẹ nhàng', 'Bình thường', 'Nặng', 'Cực nặng'],
            tickfont=dict(size=13, color='white'),
            showgrid=True,
            gridcolor='rgba(255,255,255,0.2)',
            color='white',
            range=[0.5, 4.5]
        ),
        yaxis=dict(
            title=dict(text='Mức năng lượng', font=dict(size=14)),
            range=[0, 11],
            tickfont=dict(size=13, color='white'),
            showgrid=True,
            gridcolor='rgba(255,255,255,0.2)',
            color='white'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Quicksand, sans-serif', size=13),
        hovermode='closest',
        margin=dict(t=60, b=40, l=40, r=40)
    )

    return fig
